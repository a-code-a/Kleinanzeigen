// Dokument bereit
$(document).ready(function() {
    // URL-Validierung
    $('#url').on('input', function() {
        let url = $(this).val().trim();
        
        // Automatisch https:// hinzufügen, wenn nicht vorhanden
        if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
            if (!url.startsWith('www.')) {
                url = 'www.' + url;
            }
            url = 'https://' + url;
            $(this).val(url);
        }
    });
    
    // Formular-Validierung
    $('form').on('submit', function(e) {
        let url = $('#url').val().trim();
        
        // Einfache Validierung für Kleinanzeigen-URLs
        if (!url.includes('kleinanzeigen.de/s-anzeige/')) {
            e.preventDefault();
            alert('Bitte geben Sie eine gültige Kleinanzeigen-URL ein.');
            return false;
        }
        
        // Lade-Animation anzeigen
        $('button[type="submit"]').html('<i class="fas fa-spinner fa-spin"></i> Wird geladen...');
        $('button[type="submit"]').prop('disabled', true);
    });
    
    // Bilder-Galerie
    $('.image-gallery a').on('click', function(e) {
        e.preventDefault();
        
        // Bild in neuem Tab öffnen
        window.open($(this).attr('href'), '_blank');
    });
    
    // Tooltips aktivieren
    $('[data-toggle="tooltip"]').tooltip();
});
