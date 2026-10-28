const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

test('suggestions filter by profile, all themes remain accessible, Arabic labels update', () => {
  const listeners = {};
  const gender = {value: 'girl', addEventListener: (name, fn) => listeners[name] = fn};
  const buttons = ['Fées', 'Robots', 'Science'].map(label => ({dataset: {themeLabel: label}}));
  let toggle, onLanguage;
  const document = {
    documentElement: {lang: 'fr'},
    addEventListener: (_, fn) => fn(),
    getElementById: () => gender,
    querySelector: () => ({before: el => toggle = el, querySelectorAll: () => buttons}),
    createElement: () => ({setAttribute(){}, addEventListener: (_, fn) => listeners.toggle = fn}),
  };
  vm.runInNewContext(fs.readFileSync('themes.js', 'utf8'), {document, MutationObserver: class {
    constructor(fn) {onLanguage = fn;} observe() {}
  }});
  assert.deepEqual(buttons.map(b => b.hidden), [false, true, false]);
  listeners.toggle();
  assert.ok(buttons.every(b => !b.hidden));
  gender.value = 'boy'; listeners.change();
  assert.deepEqual(buttons.map(b => b.hidden), [true, false, false]);
  document.documentElement.lang = 'ar'; onLanguage();
  assert.equal(toggle.textContent, 'عرض جميع المواضيع');
});
