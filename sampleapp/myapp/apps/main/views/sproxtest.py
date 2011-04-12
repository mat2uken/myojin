
# encoding: utf-8

import datetime
from myojin import submodule, utils as flaskext_utils
from myojin.rum import rum_response
from ....core.decorators import admin_required, admin_ip_check, login_required
from .... import current_app
from flask import request, session, make_response, app, flash
from myojin.utils import redirect, redirect_to
from ..models import User, Memo
from flask import url_for


module = submodule.SubModule(__name__, url_prefix="/sproxtest")



from myapp.models import Image
from sprox.dojo.formbase import DojoEditableForm,  DojoAddRecordForm
from flask import url_for
#from myapp.database import db_session
from formencode import validators, Invalid
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller,EditFormFiller
import formencode
#from myapp.db import session
db_session = current_app.db.session

class UniqueSlug(formencode.FancyValidator):

    model = None

    def _to_python(self, value, state):
        if not self.model is None:
            values = db_session.query(self.model.slug).first()
            if values is None:
                return value
        else:
            raise NameError('model is not defined')
        if unicode(value) in values:
            raise formencode.Invalid('That slug already exists', value, state)
        return value

class FormDefaults(DojoAddRecordForm):
    __omit_fields__ = ['id', 'discriminator', 'create_date', 'update_date']

class ImageForm(FormDefaults):
    __model__ = Image
    slug = UniqueSlug(model=Image)
    image = validators.FieldStorageUploadConverter(if_missing=None)

class EditImageForm(DojoEditableForm):
    __model__ = Image
    __omit_fields__ = ['id', 'slug']
    image = validators.FieldStorageUploadConverter(if_missing=None)

class EditImageFormFiller(EditFormFiller):
    __model__ = Image

class ImageList(TableBase):
    __model__ = Image
    __xml_fields__ = ['image']
    __omit_fields__ = ['alt_text']

class ImageListFiller(TableFiller):
    __model__ = Image

    def _do_get_provider_count_and_objs(*args, **kws):
        xs = Image.query[-3:]
        return len(xs), xs

    def __actions2__(self, obj):
        """Override this function to define how action links should be displayed for the given record."""
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div><div><a class="edit_link" href="'+str(url_for('edit_image', id=pklist))+'" style="text-decoration:none">edit</a>'\
              '</div><div>'\
              '<form method="POST" action="'+str(url_for('delete_image', id=pklist))+'" class="button-to">'\
            '<input type="hidden" name="_method" value="DELETE" />'\
            '<input class="delete-button" onclick="return confirm(\'Are you sure?\');" value="delete" type="submit" '\
            'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
        '</form>'\
        '</div></div>'
        return value

    def image(self, obj):
        image = (
            '<img width="100px" height="75px" src="%s" alt="%s" />') % (
            url_for("main.sproxtest.image", id=obj.id),
            str(obj.alt_text)
            )
        return image.join(('<div>', '</div>'))

create_image_form = ImageForm(db_session)
edit_image_form = EditImageForm(db_session)
edit_image_form_filler = EditImageFormFiller(db_session)
image_list = ImageList(db_session)
image_list_filler = ImageListFiller(db_session) 


from flask import render_template
from myojin.mako import render
render_template = render

admin = module


### Image CRUD controllers
@admin.route('/images')
@module.templated('admin_list.html')
def list_image():
    value = image_list_filler.get_value()
    return dict(image_list=image_list, name='Images', value=value, create_url=url_for('create_image'))
from flask import send_file, make_response
@admin.route('/image/<id>', methods=['GET', 'POST'])
def image(id):
    from cStringIO import StringIO
    res = make_response(Image.query.get(id=id).image or "abc", )
    res.mimetype = 'image/jpeg'
    return res
    
    return send_file(StringIO(Image.query.get(id=id).image))
    
@admin.route('/<id>/edit', methods=['GET', 'POST'])
@module.templated('admin_edit.html')
def edit_image(id):

    if request.method == 'POST':
        try:
            edit_image_form.validate(request.form)
        except Invalid as error:
            flash(error.msg)
            return redirect(url_for('create_image'))
        file = request.files['image']
        image = db_session.query(Image).get(id)
        image.alt_text = request.form['alt_text']

        if not file.filename is None:
            image.image = file.read()

        db_session.commit()
        return redirect(url_for('list_image'))

    value = edit_image_form_filler.get_value(values={'id': id})
    return dict(form=edit_image_form, name='Edit Image', value=value)
    return render_template('admin_edit.html', dict(form=edit_image_form, name='Edit Image', value=value))
from pprint import pprint
@admin.route('/create_image', methods=['GET', 'POST'])
@module.templated('admin_form.html')
def create_image():
    if request.method == 'POST':
        try:
            create_image_form.validate(request.form)
        except Invalid as error:
            flash(error.msg)
            return redirect(url_for('create_image'))
        pprint(request.form)
        try:
            file = request.files['image']
            image = Image(slug=request.form.get('slug'), alt_text=request.form.get('alt_text'), image=file.read())
            db_session.add(image)
            db_session.commit()
            flash('Image saved')
        except Exception, e:
            raise
            import traceback;traceback.print_exc()
        return redirect(url_for('list_image'))
    return dict(form=create_image_form, name='Create Image')
    return render_template('admin_form.html', dict(form=create_image_form, name='Create Image'))

@admin.route('/delete_image/<id>', methods=['GET', 'POST'])
def delete_image(id):
    image = db_session.query(Image).get(id)

    if image is None:
        flash('Image not found')
    else:
        db_session.delete(image)
        db_session.commit()
        flash('Image deleted')

    return redirect(url_for('list_image'))
