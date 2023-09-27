document.addEventListener("DOMContentLoaded", function () {
    var submitButton = document.getElementById("submit-button");
    var copyButton = document.getElementById("copy-button");
    var messageInput = document.getElementById("message-input");
    var saltInput = document.getElementById("salt-input");
    var linkElement = document.getElementById("link");
    var initialButtonText = copyButton.innerHTML;

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
                setTimeout(() => {
                    copyButton.innerHTML = initialButtonText;
                }, 5000);
            })
            .catch((error) => {
                console.error("Error:", error);
            });
    }
});
