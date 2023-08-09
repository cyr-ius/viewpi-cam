function send_cmd(cmd) {
  cmd.replace(/&/g, "%26").replace(/#/g, "%23").replace(/\+/g, "%2B");
  $.get({
    url:"cmd_pipe/" + cmd,
    success: function(data){
      if (data["type"] == "error") $('#toast').removeClass("text-bg-primary").addClass("text-bg-danger")
      $('#toast .toast-body').html(data["message"])
      liveToast.show()
    }
  });
}

var filterFloat = function (value) {
  if (/^(\-|\+)?([0-9]+(\.[0-9]+)?|Infinity)$/.test(value))
    return Number(value);
  return NaN;
};

$.fn.filterFloat = function (value) {
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

function convertFormToJSON(form) {
  return $(form)
    .serializeArray({checkboxesAsBools: true})
    .reduce(function (json, { name, value }) {
      check_value = filterFloat(value) || value;
      if (check_value == "0") check_value = 0;
      if (! json.hasOwnProperty(name) ) {
        json[name] = check_value;
      } else {
        if (Array.isArray(json[name])) {
          json[name].push(check_value)
        } else {
          pval = json[name]
          json[name] = [pval, check_value]
        }
      }
      return json;
    }, {});
}

function queryData(method="POST", url, data, callbackSuccess,callbackError){
  $.ajax({
      method: method,
      url: url,
      data: JSON.stringify(data),
      dataType:"json",
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

      var rselectTextarea = /select|textarea/i;
      var rinput = /text|hidden|password|search|number/i;

      return this.map(function () {
          return this.elements ? $.makeArray(this.elements) : this;
      })
      .filter(function () {
          return this.name && !this.disabled &&
              (this.checked || (o.checkboxesAsBools && this.type === 'checkbox')
              || rselectTextarea.test(this.nodeName)
              || rinput.test(this.type));
          })
          .map(function (i, elem) {
              var val = $(this).val();
              return val == null ?
              null :
              $.isArray(val) ?
              $.map(val, function (val, i) {
                  return { name: elem.name, value: val };
              }) :
              {
                  name: elem.name,
                  value: (o.checkboxesAsBools && this.type === 'checkbox') ?
                      (this.checked ? true : false) :
                      val
              };
          }).get();
  };

  $.fn.convertJson = function(){
    this.reduce(function (json, { name, value }) {
      check_value = filterFloat(value) || value;
      if (check_value == "0") check_value = 0;
      if (! json.hasOwnProperty(name) ) {
        json[name] = check_value;
      } else {
        if (Array.isArray(json[name])) {
          json[name].push(check_value)
        } else {
          pval = json[name]
          json[name] = [pval, check_value]
        }
      }
      return json;
    }, {});
  }

})()
