function send_cmd(cmd) {
    cmd.replace(/&/g, "%26").replace(/#/g, "%23").replace(/\+/g, "%2B");
    $.get("cmd_pipe/" + cmd)
}