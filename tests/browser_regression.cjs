// Run against a disposable local server: node tests/browser_regression.cjs
// Requires Playwright and its Chromium browser.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM_PATH ? {executablePath: process.env.CHROMIUM_PATH} : {})});
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(process.env.TEST_URL || 'http://127.0.0.1:8080');
  await page.evaluate(() => {
    navigate('quiz');
    answers = Object.fromEntries(questionsData.map(q => [q.id, 3]));
    currentStep = 4;
    renderStep();
  });
  // All displayed education choices must be accepted by the real server.
  const levels = await page.evaluate(() => educationOptions.map(opt => opt.level));
  for (const level of levels) {
    await page.evaluate(async level => { selectedEducation = level; await submitAssessment(); }, level);
    assert.equal(await page.locator('#results').isVisible(), true, level);
    assert.equal(await page.locator('#assessment-error-modal').isVisible(), false);
  }
  await page.evaluate(() => { resetQuiz(); answers = Object.fromEntries(questionsData.map(q => [q.id, 3])); currentStep = 4; renderStep(); });
  // A delayed request must remain pending without a popup or duplicate submission.
  let requests = 0;
  let release;
  await page.route('**/predict', async route => {
    requests++;
    await new Promise(resolve => { release = resolve; });
    await route.continue();
  });
  await page.locator('#btn-next').click();
  await page.waitForTimeout(300);
  await page.evaluate(() => submitAssessment());
  assert.equal(requests, 1);
  assert.equal(await page.locator('#btn-next').isDisabled(), true);
  assert.equal(await page.locator('#assessment-error-modal').isVisible(), false);
  release();
  await page.waitForFunction(() => !assessmentSubmitting);
  await page.unroute('**/predict');
  // Offline failure: one popup, preserved answers and token, explicit retry only.
  await page.evaluate(() => { resetQuiz(); answers = Object.fromEntries(questionsData.map(q => [q.id, 3])); currentStep = 4; renderStep(); });
  await page.route('**/predict', route => route.abort('internetdisconnected'));
  await page.evaluate(() => submitAssessment());
  assert.equal(await page.locator('#assessment-error-modal').isVisible(), true);
  const token = await page.evaluate(() => pendingSubmission.id);
  const savedAnswers = await page.evaluate(() => JSON.stringify(answers));
  await page.locator('#assessment-error-close').click();
  await page.waitForTimeout(500);
  assert.equal(await page.locator('#assessment-error-modal').isVisible(), false);
  await page.unroute('**/predict');
  await page.evaluate(() => submitAssessment());
  assert.equal(await page.evaluate(() => completedSubmissionId), token);
  assert.equal(await page.evaluate(() => JSON.stringify(answers)), savedAnswers);
  assert.equal(await page.locator('#results').isVisible(), true);
  // Server validation errors must not be described as a slow connection.
  await page.evaluate(() => { resetQuiz(); currentStep = 4; renderStep(); });
  await page.route('**/predict', route => route.fulfill({status: 400, contentType:'application/json', body: JSON.stringify({message:'Choose a valid goal and education level.'})}));
  await page.evaluate(() => submitAssessment());
  assert.equal(await page.locator('#assessment-error-title').textContent(), 'Please check your assessment');
  assert.match(await page.locator('#assessment-error-description').textContent(), /Choose a valid/);
  // Check viewport overflow and square icons on home, assessment and the modal.
  for (const width of [280, 320, 375, 480, 768, 1024, 1440]) {
    await page.setViewportSize({width, height: 800});
    const modal = await page.locator('#assessment-error-modal').boundingBox();
    assert.ok(modal.x >= 0 && modal.x + modal.width <= width, `modal at ${width}`);
    await page.locator('#assessment-error-close').click();
    for (const screen of ['home', 'quiz']) {
      await page.evaluate(screen => { navigate(screen); currentStep = 2; if (screen === 'quiz') renderStep(); }, screen);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `overflow ${screen} ${width}`);
      for (const icon of await page.locator('svg.line-icon:visible, .brand-mark:visible').all()) {
        const box = await icon.boundingBox();
        assert.ok(Math.abs(box.width - box.height) < 1, `square icon ${width}`);
      }
    }
    await page.evaluate(() => assessmentErrorModal.showModal());
  }
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('PASS: education submissions, delayed requests, offline retry, validation errors, and icon/layout checks at seven widths.');
})().catch(error => { console.error(error); process.exitCode = 1; });
