function send_cmd(cmd) {
  cmd.replace(/&/g, "%26").replace(/#/g, "%23").replace(/\+/g, "%2B");
  $.ajax({
    method: "POST",
    url:"/pipe_cmd",
    data: JSON.stringify({"cmd":cmd}),
    dataType:"json",
    contentType:"application/json; charset=utf-8",        
    success: function(data){
      if (data["type"] == "error") $('#toast').removeClass("text-bg-primary").addClass("text-bg-danger")
      $('#toast .toast-body').html(data["message"])
    }
  });
}

var filterFloat = function (value) {
  if (/^(\-|\+)?([0-9]+(\.[0-9]+)?|Infinity)$/.test(value))
    return Number(value);
  return NaN;
};

function populate(frm, data) {
  $.each(data, function (key, value) {
    var ctrl = $('[name=' + key + ']', frm);
    switch (ctrl.prop("type")) {
      case "radio": case "checkbox":
        ctrl.each(function () {
          if ($(this).attr('value') == value) $(this).attr("checked", value);
        });
        break;
      default:
        ctrl.val(value);
    }
  });
}

function queryData(method="POST", url, data, callbackSuccess,callbackError){
  $.ajax({
      method: method,
      url: url,
      data: JSON.stringify(data),
      // dataType:"json",
      contentType:"application/json; charset=utf-8",            
      success: function(data){
          $("#toast .toast-body").html(data["message"])
          if (callbackSuccess) callbackSuccess(data)
      },
      error: function(data){
          $("#toast .toast-body").html(data["message"])
          if (callbackError) callbackError(data)
      },
  })  
}

(() => {
  'use strict'

  // Fetch all the forms we want to apply custom Bootstrap validation styles to
  const forms = document.querySelectorAll('.needs-validation')

  // Loop over them and prevent submission
  Array.from(forms).forEach(form => {
    form.addEventListener('submit', event => {
      if (!form.checkValidity()) {
        event.preventDefault()
        event.stopPropagation()
      }

      form.classList.add('was-validated')
    }, false)
  })

  // Select the node that will be observed for mutations
  const targetNode = document.getElementById('toast');

  // Options for the observer (which mutations to observe)
  const config = { attributes: true, childList: true, subtree: true };

  // Callback function to execute when mutations are observed
  const callback = function(mutationsList, observer) {
      for(const mutation of mutationsList) {
          if (mutation.type === 'childList') {
              $.each($('.toast'), function(e) { 
                  $(this).toast("show");
                  $(this).on('hide.bs.toast', function () {
                      $(this).find('.toast-body').html("")
                  });
              })
          }
      }
  };

  // Create an observer instance linked to the callback function
  const observer = new MutationObserver(callback);

  // Start observing the target node for configured mutations
  observer.observe(targetNode, config);


  $.fn.serialize = function (options) {
    return $.param(this.serializeArray(options));
  };

  $.fn.serializeArray = function (options) {
      var o = $.extend({
          checkboxesAsBools: false
      }, options || {});

      var rCRLF = /\r?\n/g;
      var rcheckableType = /^(?:checkbox|radio)$/i;
      var rsubmitterTypes = /^(?:submit|button|image|reset|file)$/i;
      var rsubmittable = /^(?:input|select|textarea|keygen)/i;

      return this.map( function() {
        // Can add propHook for "elements" to filter or add form elements
        var elements = jQuery.prop( this, "elements" );
        return elements ? jQuery.makeArray( elements ) : this;
      } ).filter( function() {
        var type = this.type;
          return this.name && !jQuery( this ).is( ":disabled" ) &&
            rsubmittable.test( this.nodeName ) && !rsubmitterTypes.test( type );
      } ).map(function (_i, elem) {
              var val = jQuery( this ).val();
              if ( val == null ) {
                return null;
              }
              if ( Array.isArray( val ) ) {
                return jQuery.map( val, function( val ) {
                  return { name: elem.name, value: val.replace( rCRLF, "\r\n" ) };
                } );
              } else if (rcheckableType.test(this.type)) {    
                if (o.checkboxesAsBools) {
                  return {
                    name: elem.name,
                    value: (o.checkboxesAsBools &&  this.type === 'checkbox') ?
                        (this.checked ? 1 : 0) :
                        val.replace( rCRLF, "\r\n" ) 
                  } 
                } else {
                  if (this.checked)
                    return {name: elem.name, value: val.replace( rCRLF, "\r\n" )}
                }
              } else {
                return { name: elem.name, value: val.replace( rCRLF, "\r\n" ) };
              }
      } ).get();
  };

  $.fn.serializeObject = function(options){
    var o = $.extend({checkboxesAsBools: false}, options || {}) ;
    return this.serializeArray({checkboxesAsBools: o.checkboxesAsBools})
    .reduce(function(obj, item) {
      var name = item["name"]
      var check_value = filterFloat(item["value"]) || item["value"];
      if (check_value == "0") check_value = 0;
      if (! obj.hasOwnProperty(name) ) {
        obj[name] = check_value;
      } else {
        if (Array.isArray(obj[name])) {
          obj[name].push(check_value)
        } else {
          var pval = obj[name]
          obj[name] = [pval, check_value]
        }
      }
      return obj
    }, {})
  }

})()