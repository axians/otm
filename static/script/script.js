document.addEventListener("DOMContentLoaded", function () {
    var submitButton = document.getElementById("submit_button");
    var copyButton = document.getElementById("copy_button");
    var messageInput = document.getElementById("message_input");
    var saltInput = document.getElementById("salt_input");
    var linkElement = document.getElementById("link");
    var infoButton = document.getElementById("info_button");
    var infoContainer = document.getElementById("i_c");

    infoButton.addEventListener("mouseout", function () {
        infoContainer.style.display = "none";
    });
    infoButton.addEventListener("mouseover", function () {
        infoContainer.style.display = "block";
    });

    submitButton.addEventListener("click", submitMessage);
    copyButton.addEventListener("click", copyToClipboard);

    function submitMessage() {
        var message = messageInput.value;
        var salt = saltInput.value;

        fetch(document.documentURI, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message, salt})
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then((data) => {
                linkElement.innerHTML = data.message.link;
                linkElement.href = data.message.link;
                copyButton.hidden = false;
                messageInput.value = "";
                saltInput.value = "";
            })
            .catch((error) => {
                console.error("Error:", error);
            });
    }

    function copyToClipboard() {
        navigator.clipboard.writeText(linkElement.href)
            .then(() => {
                copyButton.innerHTML = "Copied!";
                //alert("Copied to clipboard!");
            })
            .catch((error) => {
                console.error("Error:", error);
            });
    }
});
