
datePick = function(elem)
{

//  jQuery(elem).datepicker();
};

jQuery("#grid").jqGrid({
      url:'getrows?model=Wine',
      datatype: "json",
      mtype: 'GET',
      colNames:['id', 'Provider', 'Name', 'Year', 'Description', 'Type', 'Geographical Region', 'Creation Date', 'Edit Date'],
      colModel:[
        {name:'id',index:'id', width:55, sortable:false, editable:false, editoptions:{readonly:true,size:10}},
        {name:'nickname',index:'user.nickname', width:200,editable:false,search:true,searchoptinos:{}},
        {name:'name',index:'name', width:200,editable:true},
        {name:'year',index:'year', width:100,editable:true},
                {name:'description',index:'description', width:300,editable:true},
                {name:'type',index:'type', width:200,editable:true,edittype:'select',editoptions:{dataUrl: '/jqGridOptionData?entity=WineType'}},
                {name:'geographical_region',index:'geographical_region', width:200,editable:true},
                {name:'creationDate',index:'creationDate', width:100},
	{name:'editDate',index:'editDate', width:100, search:true, searchoptions:{dataInit:datePick}}
           ],
     jsonReader : {
//          repeatitems:false
          repeatitems:true
     },
      rowNum:10,
      rowList:[10,20,30],
      pager: jQuery('#gridpager'),
      sortname: 'name',
      viewrecords: true,
      sortorder: "asc",
      caption:"Wines",
      editurl:"/jqGridModel?model=Wine"
			}).navGrid('#gridpager').filterToolbar({
								 stringResult:true
							       });
//jQuery("#mysearch").filterGrid('#grid',{gridModel:true});

$(function(){
  $("#list").jqGrid({
    url:'getrows',
    datatype: 'json',
    mtype: 'GET',
    colNames:['Inv No','Date', 'Amount','Tax','Total','Notes'],
    colModel :[
      {name:'invid', index:'invid', width:55},
      {name:'invdate', index:'invdate', width:90},
      {name:'amount', index:'amount', width:80, align:'right'},
      {name:'tax', index:'tax', width:80, align:'right'},
      {name:'total', index:'total', width:80, align:'right'},
      {name:'note', index:'note', width:150, sortable:false}
    ],
    pager: '#pager',
    rowNum:10,
    rowList:[10,20,30],
    sortname: 'invid',
    sortorder: 'desc',
    viewrecords: true,
    caption: 'My first grid'
  });
});
