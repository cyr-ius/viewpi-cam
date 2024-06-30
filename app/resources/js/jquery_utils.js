// Main functions
"use strict";
// *** Bootstrap Validation ***
// Fetch all the forms we want to apply custom Bootstrap validation styles to
const forms = document.querySelectorAll(".needs-validation");

// Loop over them and prevent submission
Array.from(forms).forEach((form) => {
  form.addEventListener(
    "submit",
    (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    },
    false,
  );
});

// *** Div Validation ***
// Loop over them and prevent submission
Array.from(forms).forEach((div) => {
  div.addEventListener(
    "submit-line",
    (event) => {
      let fields = div.querySelectorAll("input, select, textarea");
      Array.from(fields).forEach((field) => {
        if (!field.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
      });
      div.classList.add("was-validated");
    },
    false,
  );
});

// *** Observer Toast ***
// Callback function to execute when mutations are observed
const callback = function (mutationsList, observer) {
  for (const mutation of mutationsList) {
    if (mutation.type === "childList") {
      $.each($(".toast"), function (e) {
        $(this).toast("show");
        $(this).on("hide.bs.toast", function () {
          $(this).find(".toast-body").html("");
          $(this).removeClass("text-bg-primary text-bg-warning text-bg-danger");
        });
      });
    }
  }
};
// Select the node that will be observed for mutations
// Create an observer instance linked to the callback function
// Options for the observer (which mutations to observe)
const targetNode = document.getElementById("toast");
const config = { attributes: true, childList: true, subtree: true };
const observer = new MutationObserver(callback);
// Start observing the target node for configured mutations
observer.observe(targetNode, config);

// *** Global functions ***
// Display Toast message
$.msgToToast = function (options) {
  var o = $.extend({ category: "success", msg: null }, options || {});
  if (o.category == "success") $("#toast").addClass("text-bg-primary");
  if (o.category == "error") $("#toast").addClass("text-bg-danger");
  if (o.category == "warning") $("#toast").addClass("text-bg-warning");

  $("#toast .toast-body").html(o.msg);
};
// Toggle Spinner display
$.spinner = function (options) {
  var o = $.extend({ status: null }, options || {});
  if (o.status) {
    $(".bi-eye").addClass("d-none");
    $(".spinner-border").removeClass("d-none");
  } else {
    $(".bi-eye").removeClass("d-none");
    $(".spinner-border").addClass("d-none");
  }
};
// Ajax advanced function
$.queryData = function (options) {
  var o = $.extend(
    {
      method: "POST",
      url: null,
      data: null,
      success: null,
      error: null,
      contentType: "application/json; charset=utf-8",
      xhrFields: null,
      display_success: true,
      display_error: true,
      display_spinner: true,
      processData: true,
    },
    options || {},
  );

  if (
    o.contentType == "application/json; charset=utf-8" &&
    o.data != "" &&
    o.method.toUpperCase() != "GET"
  )
    o.data = JSON.stringify(o.data);

  $.ajax({
    method: o.method,
    url: o.url,
    data: o.data,
    contentType: o.contentType,
    xhrFields: o.xhrFields,
    processData: o.processData,
    beforeSend: function (data) {
      if (o.display_spinner) $.spinner({ status: true });
    },
    success: function (data, response, xhr) {
      if (o.display_error) {
        if (data && data.responseJSON)
          $.msgToToast({
            category: "success",
            msg: data.responseJSON["message"],
          });
      }
      if (o.success) return o.success(data, response, xhr);
    },
    error: function (data, response, xhr) {
      if (o.display_error) {
        if (data && data.responseJSON) {
          $.msgToToast({
            category: "error",
            msg: data.responseJSON["message"],
          });
        } else {
          $.msgToToast({ category: "error", msg: data["message"] });
        }
      }
      if (o.error) return o.error(data, response, xhr);
    },
    complete: function (xhr, status) {
      $.spinner({ status: false });
    },
  });
};
// Check is_number
$.filterFloat = function (value) {
  if (/^(\-|\+)?([0-9]+(\.[0-9]+)?|Infinity)$/.test(value))
    return Number(value);
  return NaN;
};
// Send command to raspiconfig
$.sendCmd = function (options) {
  var o = $.extend(
    {
      url: "{{url_for('api.system_command')}}",
      cmd: null,
      params: null,
      success: null,
      error: null,
    },
    options || {},
  );
  if (typeof o.params === "string" || o.params instanceof String) {
    o.params = [o.params];
  }
  $.queryData({
    url: o.url,
    data: { cmd: o.cmd, params: o.params },
    success: o.success,
    error: o.error,
  });
};
// Serialize form to array
$.fn.serialize = function (options) {
  return $.param(this.serializeArray(options));
};
// Serialize Array function
$.fn.serializeArray = function (options) {
  var o = $.extend(
    {
      checkboxesAsBools: false,
    },
    options || {},
  );

  var rCRLF = /\r?\n/g;
  var rcheckableType = /^(?:checkbox|radio)$/i;
  var rsubmitterTypes = /^(?:submit|button|image|reset|file)$/i;
  var rsubmittable = /^(?:input|select|textarea|keygen)/i;

  return this.map(function () {
    // Can add propHook for "elements" to filter or add form elements
    var elements = jQuery.prop(this, "elements");
    return elements ? jQuery.makeArray(elements) : this;
  })
    .filter(function () {
      var type = this.type;
      return (
        this.name &&
        !jQuery(this).is(":disabled") &&
        rsubmittable.test(this.nodeName) &&
        !rsubmitterTypes.test(type)
      );
    })
    .map(function (_i, elem) {
      var val = jQuery(this).val();
      if (val == null) {
        return null;
      }
      if (Array.isArray(val)) {
        return jQuery.map(val, function (val) {
          return { name: elem.name, value: val.replace(rCRLF, "\r\n") };
        });
      } else if (rcheckableType.test(this.type)) {
        if (o.checkboxesAsBools) {
          return {
            name: elem.name,
            value:
              o.checkboxesAsBools && this.type === "checkbox"
                ? this.checked
                  ? 1
                  : 0
                : val.replace(rCRLF, "\r\n"),
          };
        } else {
          if (this.checked)
            return { name: elem.name, value: val.replace(rCRLF, "\r\n") };
        }
      } else {
        return { name: elem.name, value: val.replace(rCRLF, "\r\n") };
      }
    })
    .get();
};
// Serialize form to object (dict)
$.fn.serializeObject = function (options) {
  var o = $.extend({ checkboxesAsBools: false }, options || {});
  return this.serializeArray({
    checkboxesAsBools: o.checkboxesAsBools,
  }).reduce(function (obj, item) {
    var name = item["name"];
    var check_value = $.filterFloat(item["value"]) || item["value"];
    if (check_value == "0") check_value = 0;
    if (!obj.hasOwnProperty(name)) {
      obj[name] = check_value;
    } else {
      if (Array.isArray(obj[name])) {
        obj[name].push(check_value);
      } else {
        var pval = obj[name];
        obj[name] = [pval, check_value];
      }
    }
    return obj;
  }, {});
};
// Clear form fields
$.fn.clearFields = function (options) {
  this.find(":input")
    .not(":button, :submit, :reset, :hidden, :checkbox, :radio")
    .val("");
  this.find(":checkbox, :radio").prop("checked", false);
};
