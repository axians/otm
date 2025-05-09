document.addEventListener("DOMContentLoaded", function () {
    const submitButton = document.getElementById("submit-button");
    const submitMessage = document.getElementById("submit-message");
    const deniedMessage = document.getElementById("denied-message");
    const copyButton = document.getElementById("copy-button");
    const messageInput = document.getElementById("message-input");
    const saltInput = document.getElementById("salt-input");
    const ttlInput = document.getElementById("ttl-input");
    const linkElement = document.getElementById("link");
    const pinElement = document.getElementById("pin");
    const pinCodeElement = document.getElementById("pin-code");
    const techHelpToggler = document.getElementById("tht");
    const shortMain = document.getElementById("main-short");
    const shortTech = document.getElementById("tech-short");
    const helpMain = document.getElementById("main-help");
    const helpTech = document.getElementById("tech-help");
    const initialMessageValue = messageInput.value;
    const initialButtonText = copyButton.innerHTML;

    techHelpToggler.checked = false
    helpTech.style.display = "none";
    deniedMessage.style.display = "none";
    shortTech.style.display = "none";

    techHelpToggler.addEventListener("change", function() {
        if(techHelpToggler.checked) {
            shortTech.style.display = "";
            shortMain.style.display = "none";
            helpTech.style.display = "";
            helpMain.style.display = "none";
        } else {
            shortTech.style.display = "none";
            shortMain.style.display = "";
            helpTech.style.display = "none";
            helpMain.style.display = "";
        }

    });

    submitButton.addEventListener("click", async () => {
        try {
            const message = messageInput.value;
            const salt = saltInput.value;
            const ttl = ttlInput.value;
            const newSalt = await generateSalt();
            const requirePin = pinElement.checked;

            const response = await fetch(document.documentURI, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message, salt, ttl, requirePin })
            });

            if (!response.ok) {
                throw new Error("Network response was not ok");
            }

            const data = await response.json();
            console.log("Response:", data);
            linkElement.innerHTML = data.message.link;
            linkElement.href = data.message.link;
            if (data.message.pin) {
                pinCodeElement.innerHTML = "PIN: " + data.message.pin;
            }
            else {
                pinCodeElement.innerHTML = "";
            }
            copyButton.hidden = false;
            messageInput.value = initialMessageValue;
            saltInput.value = newSalt;
        } catch (error) {
            console.error("Error:", error);
            submitMessage.style.display = "none";
            deniedMessage.style.display = "block";
        }
    });

    async function generateSalt() {
        try {
            const response = await fetch('https://en.wikipedia.org/api/rest_v1/page/random/title');

            if (!response.ok) {
                throw new Error('Failed to fetch random page');
            }

            const data = await response.json();
            const title = data.items[0].title;
            const salt = title.replace(/[^a-zA-Z0-9]/g, '');
            return salt;
        } catch (error) {
            console.error("Error:", error);
            throw error;
        }
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

    copyButton.addEventListener("click", copyToClipboard);
});
