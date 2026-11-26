(function () {
  'use strict';

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var area = document.createElement('textarea');
      area.value = text;
      area.style.position = 'fixed';
      area.style.opacity = '0';
      document.body.appendChild(area);
      area.select();
      try {
        if (document.execCommand('copy')) {
          resolve();
        } else {
          reject(new Error('copy failed'));
        }
      } catch (error) {
        reject(error);
      }
      document.body.removeChild(area);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var blocks = document.querySelectorAll('.post-content pre');
    Array.prototype.forEach.call(blocks, function (pre) {
      var code = pre.querySelector('code');
      if (!code) return;

      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-btn';
      button.textContent = '复制';
      button.addEventListener('click', function () {
        copyText(code.textContent).then(function () {
          button.textContent = '已复制';
          setTimeout(function () {
            button.textContent = '复制';
          }, 1500);
        });
      });
      pre.appendChild(button);
    });
  });
})();
