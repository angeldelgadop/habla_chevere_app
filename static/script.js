let mediaRecorder;
let audioChunks = [];
let currentBlob = null;

document.getElementById("recordBtn").onclick = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = event => audioChunks.push(event.data);

    mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        currentBlob = audioBlob;
        const audioUrl = URL.createObjectURL(audioBlob);
        document.getElementById("audioPlayer").src = audioUrl;
        document.getElementById("downloadLink").href = audioUrl;
        document.getElementById("downloadLink").download = "grabacion.wav";
        document.getElementById("downloadLink").style.display = "inline";
        sendAudio(audioBlob);
    };

    mediaRecorder.start();
    document.getElementById("recordBtn").disabled = true;
    document.getElementById("stopBtn").disabled = false;
};

document.getElementById("stopBtn").onclick = () => {
    mediaRecorder.stop();
    document.getElementById("recordBtn").disabled = false;
    document.getElementById("stopBtn").disabled = true;
};

function sendAudio(blob) {
    const formData = new FormData();
    formData.append("file", blob);
    formData.append("lang", document.getElementById("langSelect").value);

    fetch("/process-audio", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("output").innerHTML = `
            <p><strong>Transcripción:</strong><br>${data.transcription}</p>
            <p><strong>Feedback:</strong><br>${data.feedback}</p>
        `;
    })
    .catch(err => {
        document.getElementById("output").innerText = "❌ Error al procesar el audio.";
    });
}
