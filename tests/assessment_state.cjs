// No extra dependencies: node tests/assessment_state.cjs
const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const nodes = new Map();
function element(id) {
  if (!nodes.has(id)) nodes.set(id, {hidden: id === 'results', style: {}, disabled: false,
    textContent: '', open: false, shows: 0, addEventListener() {}, querySelector() {return element(id + '-span');},
    close() {this.open = false;}, showModal() {this.open = true; this.shows++;}});
  return nodes.get(id);
}
const sandbox = {console, AbortController, setTimeout, clearTimeout, TypeError,
  document: {getElementById: element},
  createToken: () => 'test_submission_token',
  renderPaginatedResults() {}, scrollToPageTop() {}, postFeedback: async () => {},
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('app/static/js/assessment.js', 'utf8'), sandbox);
vm.runInContext('renderStep = () => {}; answers = {R1: 3};', sandbox);
const run = expression => vm.runInContext(expression, sandbox);
(async () => {
  let payload;
  sandbox.apiFetch = async (url, options) => {payload = JSON.parse(options.body); return {json: async () => ({status:'success', recommendations:[]})};};
  await run('submitAssessment()');
  assert.equal(payload.education, 'Junior High School');
  assert.equal(element('results').hidden, false);
  assert.equal(element('assessment-error-modal').shows, 0);
  run('clearTimeout(dwellTimer); document.getElementById("results").hidden = true');
  sandbox.apiFetch = async () => { throw new TypeError('Failed to fetch'); };
  await run('submitAssessment()');
  assert.equal(element('assessment-error-modal').shows, 1);
  assert.match(element('assessment-error-description').textContent, /could not reach the server/);
  assert.equal(run('answers.R1'), 3);
  const token = run('pendingSubmission.id');
  element('assessment-error-modal').close();
  await new Promise(resolve => setTimeout(resolve, 30));
  assert.equal(element('assessment-error-modal').open, false);
  let release;
  let requests = 0;
  sandbox.apiFetch = () => {requests++; return new Promise(resolve => {release = () => resolve({json: async () => ({status:'success', recommendations:[]})});});};
  const pending = run('submitAssessment()');
  await run('submitAssessment()');
  assert.equal(requests, 1);
  assert.equal(element('btn-next').disabled, true);
  assert.equal(element('assessment-error-modal').open, false);
  release(); await pending;
  assert.equal(run('completedSubmissionId'), token);
  run('clearTimeout(dwellTimer)');
  for (const status of [400, 403, 409, 429, 500]) {
    sandbox.apiFetch = async () => {throw Object.assign(new Error('Invalid choice'), {status, retryAfter: 12});};
    await run('submitAssessment()');
    assert.doesNotMatch(element('assessment-error-description').textContent, /connection may be slow/);
    assert.equal(element('btn-next').disabled, false);
  }
  sandbox.apiFetch = async () => {throw Object.assign(new Error('Aborted'), {name:'AbortError'});};
  await run('submitAssessment()');
  assert.match(element('assessment-error-description').textContent, /took too long/);
  console.log('PASS: default education, successful submission, offline failure, no unsolicited reopening, duplicate guard, retry identity, HTTP errors and timeout.');
})().catch(error => {console.error(error); process.exitCode = 1;});
