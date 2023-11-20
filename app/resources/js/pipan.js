// mode=1 pipan, 2=servoblaster
var mode = 0;

var pan = 100;
var tilt = 100;
var cmd = "";
var pan_bak = 100;
var tilt_bak = 100;
var pan_start;
var tilt_start;
var touch = false;
var led_stat = false;
var ajax_pipan;
var pipan_mouse_x;
var pipan_mouse_y;

$(document).ready(function () {
  ajax_pipan_done();
});

$(document).keypress(function (e) {
  console.log(e.keyCode);
  pipan_onkeypress(e);
});

function ajax_pipan_done() {
  if (touch) {
    if (pan_bak != pan || tilt_bak != tilt) {
      ajax_pipan_start();
    } else {
      setTimeout("ajax_pipan_done()", 100);
    }
  }
}

function ajax_pipan_start() {
  if (mode == 1) $.get("/pipan?pan=" + pan + "&tilt=" + tilt);
  else if (mode == 2) $.get("/pipan?action=" + cmd);

  pan_bak = pan;
  tilt_bak = tilt;
}

$("#arrowLeft, #arrowRight, #arrowUp, #arrowDown").unbind();
$("#arrowLeft, #arrowRight, #arrowUp, #arrowDown").click(function () {
  cmd = $(this).attr("cmd");
  if (cmd == "up" && pan <= 190) pan += 10;
  if (cmd == "down" && pan >= 10) pan -= 10;
  if (cmd == "left" && tilt >= 10) tilt -= 10;
  if (cmd == "right" && tilt <= 190) tilt += 10;

  ajax_pipan_start();
  $(this).addClass("text-success");
  var btn = $(this);
  window.setTimeout(function () {
    clear_arrow(btn);
  }, 100);
});

function clear_arrow(btn) {
  btn.removeClass("text-success");
}

function led_switch() {
  if (!led_stat) {
    led_stat = true;
    $.get(
      "/pipan?red=" +
        $("#pilight_r").val() +
        "&green=" +
        $("#pilight_g").val() +
        "&blue=" +
        $("#pilight_b").val(),
    );
  } else {
    led_stat = false;
    $.get("/pipan?red=0&green=0&blue=0");
  }
}

function pipan_onkeypress(e) {
  if (e.keyCode == 97) $("#arrowLeft").trigger("click");
  else if (e.keyCode == 119) $("#arrowUp").trigger("click");
  else if (e.keyCode == 100) $("#arrowRight").trigger("click");
  else if (e.keyCode == 115) $("#arrowDown").trigger("click");
  else if (e.keyCode == 102) led_switch();
}

function pipan_start() {
  pipan_mouse_x = null;
  pipan_mouse_y = null;
  pan_start = pan;
  tilt_start = tilt;
  document.body.addEventListener("touchmove", pipan_move, false);
  document.body.addEventListener("touchend", pipan_stop, false);
  touch = true;
  ajax_pipan_start();
}

function pipan_move(e) {
  var ev = e;

  if (pipan_mouse_x == null) {
    pipan_mouse_x = e.changedTouches[0].pageX;
    pipan_mouse_y = e.changedTouches[0].pageY;
  }
  mouse_x = e.changedTouches[0].pageX;
  mouse_y = e.changedTouches[0].pageY;
  e.preventDefault();

  var pan_temp = pan_start + Math.round((mouse_x - pipan_mouse_x) / 5);
  var tilt_temp = tilt_start + Math.round((pipan_mouse_y - mouse_y) / 5);
  if (pan_temp > 200) pan_temp = 200;
  if (pan_temp < 0) pan_temp = 0;
  if (tilt_temp > 200) tilt_temp = 200;
  if (tilt_temp < 0) tilt_temp = 0;

  pan = pan_temp;
  tilt = tilt_temp;
}

function pipan_stop() {
  document.body.removeEventListener("touchmove", pipan_move, false);
  document.body.removeEventListener("touchend", pipan_stop, false);
  touch = false;
}

function init_pt(p, t) {
  pan = p;
  tilt = t;
}

function set_panmode(m) {
  mode = m;
}
