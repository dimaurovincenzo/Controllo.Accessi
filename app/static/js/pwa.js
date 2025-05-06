// Registrazione del Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/static/js/service-worker.js')
      .then(function(registration) {
        console.log('Service Worker registrato con successo con scope: ', registration.scope);
      })
      .catch(function(error) {
        console.log('Registrazione Service Worker fallita: ', error);
      });
  });
}

// Gestione dell'installazione dell'app
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // Impedisci al browser di mostrare automaticamente il prompt
  e.preventDefault();
  // Salva l'evento per poterlo attivare più tardi
  deferredPrompt = e;

  // Aggiorna l'interfaccia utente per informare l'utente che può installare la PWA
  const installBtn = document.getElementById('install-button');
  if (installBtn) {
    installBtn.style.display = 'block';
    
    installBtn.addEventListener('click', (e) => {
      // Mostra il prompt di installazione
      deferredPrompt.prompt();
      // Aspetta che l'utente risponda al prompt
      deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('L\'utente ha accettato di installare l\'app');
        } else {
          console.log('L\'utente ha rifiutato di installare l\'app');
        }
        deferredPrompt = null;
        // Nascondi il pulsante, non è più necessario
        installBtn.style.display = 'none';
      });
    });
  }
}); 