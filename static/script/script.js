document.addEventListener("DOMContentLoaded", function () {
    var submitButton = document.getElementById("submit_button");
    var copyButton = document.getElementById("copy_button");
    var messageInput = document.getElementById("message_input");
    var linkElement = document.getElementById("link");

    submitButton.addEventListener("click", submitMessage);
    copyButton.addEventListener("click", copyToClipboard);

    function submitMessage() {
        var message = messageInput.value;

        fetch(document.documentURI, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message })
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
