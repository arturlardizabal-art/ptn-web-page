(() => {
  'use strict';
  const en = document.documentElement.lang.startsWith('en');
  const header = document.querySelector('.site-header');
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#site-nav');
  if (header && toggle && nav) {
    header.classList.add('js-ready');
    const setMenu = open => {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', en ? (open ? 'Close menu' : 'Open menu') : (open ? 'Cerrar menú' : 'Abrir menú'));
      nav.classList.toggle('is-open', open);
    };
    const close = () => setMenu(false);
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      setMenu(open);
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {close();toggle.focus();} });
    nav.addEventListener('click', e => {if(e.target.closest('a'))close();});
  }
  const form = document.querySelector('#quote-form');
  if (form) {
    form.querySelector('button[type=submit]').disabled = false;
    const select = form.querySelector('[name=servicio]');
    const requested = new URLSearchParams(location.search).get('servicio');
    if (requested && Array.from(select.options).some(o => o.value === requested)) select.value = requested;
    form.addEventListener('submit', e => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const service = select.options[select.selectedIndex].textContent;
      const lines = [en ? 'Hello PTN, I would like a quote.' : 'Hola PTN, me gustaría solicitar una cotización.',
        `${en ? 'Name' : 'Nombre'}: ${data.get('nombre')}`,
        `${en ? 'Company' : 'Empresa'}: ${data.get('empresa')}`,
        `Email: ${data.get('email')}`,
        `${en ? 'Phone' : 'Teléfono'}: ${data.get('telefono') || '—'}`,
        `${en ? 'Service' : 'Servicio'}: ${service}`,
        `${en ? 'Quantity' : 'Cantidad'}: ${data.get('cantidad') || '—'}`,
        `${en ? 'Delivery city' : 'Ciudad de entrega'}: ${data.get('ciudad')}`,
        '', data.get('mensaje') || ''];
      const destination = `https://wa.me/528120288728?text=${encodeURIComponent(lines.join('\n'))}`;
      const status = document.querySelector('#form-status');
      status.replaceChildren();
      const link = document.createElement('a'); link.href = destination; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.textContent = en ? 'Open your prepared request in WhatsApp' : 'Abrir tu solicitud preparada en WhatsApp';
      status.append(document.createTextNode(en ? 'Your request is prepared. Send it from WhatsApp: ' : 'Tu solicitud está preparada. Envíala desde WhatsApp: '),link);
      const popup = window.open(destination, '_blank', 'noopener,noreferrer');
      if (popup) popup.opener = null;
      // Preparing a draft is not a confirmed lead or a message sent.
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({ event:'quote_draft_prepared', service:select.value, page_path:location.pathname, lang:document.documentElement.lang });
    });
  }
  document.addEventListener('click', e => {
    const link = e.target.closest('a[data-track]'); if (!link) return;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({event:link.dataset.track,service:link.dataset.service || document.body.dataset.service || '',page_path:location.pathname,lang:document.documentElement.lang});
  });
})();
