import tw2.core
import tw2.forms
class Movie(tw2.forms.FormPage):
    title = 'Movie'
    resources = [tw2.core.CSSLink(filename='myapp.css')]
    class child(tw2.forms.TableForm):
        title = tw2.forms.TextField(validator=tw2.core.Required)
        director = tw2.forms.TextField()
        genre = tw2.forms.CheckBoxList(options=['Action', 'Comedy', 'Romance', 'Sci-fi'])
        class cast(tw2.forms.GridLayout):
            extra_reps = 5
            character = tw2.forms.TextField()
            actor = tw2.forms.TextField()

class Index(tw2.core.Page):
    template = 'genshi:./index.html'
    def fetch_data(self, req):
        self.req = str(req)
    
tw2.core.dev_server()
