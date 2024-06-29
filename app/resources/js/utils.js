// Javascript functions
function openFullscreen() {
  if (elem.requestFullscreen) {
    elem.requestFullscreen();
  } else if (elem.webkitRequestFullscreen) {
    /* Safari */
    elem.webkitRequestFullscreen();
  }
}

function closeFullscreen() {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.webkitExitFullscreen) {
    /* Safari */
    document.webkitExitFullscreen();
  }
}

function toggleFullscreen(event) {
  let background = document.getElementById("background");

  if (!background) {
    background = document.createElement("div");
    background.id = "background";
    document.body.appendChild(background);
  }

  if (event.className == "fullscreen") {
    event.className = "img-fluid standard";
    background.style.display = "none";
    closeFullscreen();
  } else {
    event.className = "fullscreen";
    background.style.display = "block";
    openFullscreen();
  }
}
