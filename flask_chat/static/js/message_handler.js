// initialising socket connection
const socket = io.connect("http://" + document.location.hostname + ":5000/");
var messagesLoaded;

// number of overall loaded messages on the page - works as counter
function initCounter(counter) {
  messagesLoaded = counter;
}

// converts timestamps to readable time format
document.addEventListener("DOMContentLoaded", function () {
  const timestamps = document.querySelectorAll(".timestamp");
  timestamps.forEach(function (timestampElement) {
    const rawTimestamp = timestampElement.getAttribute("data-timestamp");
    const formattedTimestamp = getTime(parseFloat(rawTimestamp) * 1000);
    timestampElement.textContent = formattedTimestamp;
  });
});

// triggered when no more messages to load - then "load more" button disappears
socket.on("loading_finished", function () {
  const loadButton = document.getElementById("l");
  loadButton.style.display = "none";
});

// receives group of messages with "load more" button
socket.on("load", function (msg) {
  var nestedDiv = $("<div>").append(
    $("<p>").text(msg.username),
    $("<p>").text(msg.message),
    $("<p>").text(getTime(parseFloat(msg.timestamp) * 1000))
  );

  // inserts loaded messages before the existing list
  $("#messages").prepend(nestedDiv);
  messagesLoaded = (parseInt(messagesLoaded, 10) + 1).toString();
});

// displays messages received from socket
socket.on("message", function (msg) {
  var timestamp = Date.now();
  var nestedDiv = $("<div>").append(
    $("<p>").text(msg.username),
    $("<p>").text(msg.message),
    $("<p>").text(getTime(timestamp))
  );

  // adds received messages to list
  $("#messages").append(nestedDiv);
  messagesLoaded = (parseInt(messagesLoaded, 10) + 1).toString();
});

// formats posix timestamp to normal date
function getTime(time) {
  var dateObject = new Date(time);

  // formats the time components to ensure two digits
  hours = String(dateObject.getHours()).padStart(2, "0");
  minutes = String(dateObject.getMinutes()).padStart(2, "0");
  seconds = String(dateObject.getSeconds()).padStart(2, "0");

  // creates a string representing the time
  let formattedTime = `${hours}:${minutes}:${seconds}`;
  return formattedTime;
}

// send request to database to load messages with socket
function reqMessages() {
  socket.emit("request_message", messagesLoaded);
}

// sends messages to server with socket - the server log them into database
function sendMessage(username) {
  var message = $("#m").val();
  if (message.trim() !== "") {
    socket.emit("message", {
      message: message,
      username: username,
    });
    $("#m").val("");
  }
}
