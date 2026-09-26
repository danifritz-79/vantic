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
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function kachelHtml(r) {
    var tags = r.tags.map(function (t) { return '<span class="kachel-tag">' + escHtml(label(t)) + '</span>'; }).join('');
    return (
      '<button type="button" class="kachel" data-tags="' + r.tags.join(' ') + '" data-id="' + r.id + '">' +
      '<p class="kachel-titel">' + escHtml(r.titel) + '</p>' +
      (tags ? '<div class="kachel-tags">' + tags + '</div>' : '') +
      '</button>'
    );
  }

  function detailHtml(r) {
    var hashtags = r.tags.map(function (t) { return '#' + t; }).join(' ');
    return (
      '<article class="rezept" id="modal-titel">' +
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
      var grid = document.getElementById('grid');
      var leer = document.getElementById('leer');
      var overlay = document.getElementById('overlay');
      var modalInhalt = document.getElementById('modal-inhalt');

      if (rezepte.length === 0) {
        leer.hidden = false;
        return;
      }

      var nachId = {};
      rezepte.forEach(function (r) { nachId[r.id] = r; });

      grid.innerHTML = rezepte.map(kachelHtml).join('');

      function oeffnen(id) {
        var r = nachId[id];
        if (!r) return;
        modalInhalt.innerHTML = detailHtml(r);
        overlay.hidden = false;
        document.body.style.overflow = 'hidden';
        history.replaceState(null, '', '#' + id);
      }
      function schliessen() {
        overlay.hidden = true;
        document.body.style.overflow = '';
        history.replaceState(null, '', location.pathname);
      }

      grid.addEventListener('click', function (ev) {
        var btn = ev.target.closest('.kachel');
        if (btn) oeffnen(btn.getAttribute('data-id'));
      });
      document.getElementById('modal-schliessen').addEventListener('click', schliessen);
      overlay.addEventListener('click', function (ev) {
        if (ev.target === overlay) schliessen();
      });
      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape' && !overlay.hidden) schliessen();
      });

      if (location.hash) {
        var id = location.hash.slice(1);
        if (nachId[id]) oeffnen(id);
      }

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
        var kacheln = Array.prototype.slice.call(grid.querySelectorAll('.kachel'));
        var keineTreffer = document.getElementById('keine-treffer');
        var aktiv = [];

        function anwenden() {
          var sichtbar = 0;
          kacheln.forEach(function (k) {
            var tags = (k.getAttribute('data-tags') || '').split(/\s+/);
            var passt = aktiv.every(function (f) { return tags.indexOf(f) !== -1; });
            k.style.display = passt ? '' : 'none';
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
