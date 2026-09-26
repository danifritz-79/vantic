(function () {
  var KATEGORIE_NAMEN = {
    vorspeise: 'Vorspeisen',
    sauce: 'Saucen',
    dessert: 'Desserts',
    vegetarisch: 'Vegetarisch',
  };

  function label(tag) {
    return KATEGORIE_NAMEN[tag] || (tag.charAt(0).toUpperCase() + tag.slice(1));
  }

  function escHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function karte(r) {
    var hashtags = r.tags.map(function (t) { return '#' + t; }).join(' ');
    return (
      '<article class="rezept" id="' + r.id + '" data-tags="' + r.tags.join(' ') + '">' +
      '<h2>' + escHtml(r.titel) + '</h2>' +
      (r.angaben ? '<p class="angaben">' + escHtml(r.angaben) + '</p>' : '') +
      (hashtags ? '<p class="hashtags">' + escHtml(hashtags) + '</p>' : '') +
      '<div class="rezept-grid">' +
      '<div class="zutaten"><h3>Zutaten</h3>' + r.zutaten_html + '</div>' +
      '<div class="zubereitung"><h3>Zubereitung</h3>' + r.zubereitung_html +
      (r.notiz ? '<p class="notiz">Notiz: ' + escHtml(r.notiz) + '</p>' : '') +
      '</div>' +
      '</div>' +
      '</article>'
    );
  }

  fetch('rezepte.json')
    .then(function (res) { return res.json(); })
    .then(function (data) {
      var rezepte = data.rezepte || [];
      var liste = document.getElementById('rezepte-liste');
      var leer = document.getElementById('leer');

      if (rezepte.length === 0) {
        leer.hidden = false;
        return;
      }

      liste.innerHTML = rezepte.map(karte).join('');

      var inhalt = document.getElementById('inhalt');
      inhalt.innerHTML = rezepte.map(function (r) {
        return '<a href="#' + r.id + '">' + escHtml(r.titel) + '</a>';
      }).join('');
      inhalt.hidden = false;

      var alleTags = [];
      rezepte.forEach(function (r) {
        r.tags.forEach(function (t) { if (alleTags.indexOf(t) === -1) alleTags.push(t); });
      });

      if (alleTags.length > 0) {
        var filter = document.getElementById('filter');
        var html = '<button type="button" class="filter-btn is-active" data-filter="alle">Alle</button>';
        html += alleTags.map(function (t) {
          return '<button type="button" class="filter-btn" data-filter="' + t + '">' + escHtml(label(t)) + '</button>';
        }).join('');
        filter.innerHTML = html;
        filter.hidden = false;

        var buttons = Array.prototype.slice.call(filter.querySelectorAll('.filter-btn'));
        var artikel = Array.prototype.slice.call(liste.querySelectorAll('.rezept'));
        var keineTreffer = document.getElementById('keine-treffer');
        var aktiv = [];

        function anwenden() {
          var sichtbar = 0;
          artikel.forEach(function (a) {
            var tags = (a.getAttribute('data-tags') || '').split(/\s+/);
            var passt = aktiv.every(function (f) { return tags.indexOf(f) !== -1; });
            a.hidden = !passt;
            if (passt) sichtbar++;
          });
          keineTreffer.hidden = sichtbar !== 0;
        }

        buttons.forEach(function (btn) {
          btn.addEventListener('click', function () {
            var f = btn.getAttribute('data-filter');
            var alleBtn = filter.querySelector('[data-filter="alle"]');
            if (f === 'alle') {
              aktiv = [];
              buttons.forEach(function (b) { b.classList.remove('is-active'); });
              btn.classList.add('is-active');
            } else {
              alleBtn.classList.remove('is-active');
              var i = aktiv.indexOf(f);
              if (i === -1) { aktiv.push(f); btn.classList.add('is-active'); }
              else { aktiv.splice(i, 1); btn.classList.remove('is-active'); }
              if (aktiv.length === 0) alleBtn.classList.add('is-active');
            }
            anwenden();
          });
        });
      }
    })
    .catch(function () {
      document.getElementById('leer').hidden = false;
    });
})();
