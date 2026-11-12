// No extra dependencies: node tests/career_cards.cjs
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const context = vm.createContext({URL, console, setTimeout, clearTimeout});
for (const name of ['api-client', 'program-search', 'career-results']) {
  vm.runInContext(fs.readFileSync(`app/static/js/${name}.js`, 'utf8'), context);
}
function render(expression, item) {context.item = item; return vm.runInContext(expression, context);}
const item = {title:'Sample career', salary:'PHP 18,174 / month (survey average; PSA 2022)', salary_reference:{match_type:'related', measure:'survey_average', year:2022, source_name:'PSA', source_url:'https://example.org/pay', mapping_note:'Related occupation proxy.'}};
let html = render('renderSalaryReference(item)', item);
assert.ok(html.indexOf('PHP 18,174 / month') < html.indexOf('</summary>'));
assert.doesNotMatch(html,/career-salary-amount|<strong/);
assert.match(html, /Related-role estimate/);
assert.match(html, /Historical 2022 survey/);
assert.ok(html.indexOf('https://example.org/pay') > html.indexOf('<details'));
assert.doesNotMatch(html, /<details[^>]*\bopen\b/);
html = render('renderSalaryReference(item)', {...item, salary:'', salary_reference:{match_type:'unavailable'}});
assert.match(html, /Not available/);
assert.doesNotMatch(html, /PHP [0-9]/);
html = render('programLinks(item, 2, "college")', {college_options:[{name:'Nursing'}]});
assert.doesNotMatch(html, /<details/);
assert.match(html, /Nursing/);
html = render('programLinks(item, 2, "college")', {college_options:[{name:'Nursing'},{name:'Public Health'}]});
assert.match(html, /class="career-program-toggle"/);
assert.match(html, /Show 1 more college programs/);
assert.match(html, /id="program-options-2-college"[^>]*hidden/);
assert.match(html, /Public Health/);
assert.match(html, /followStudyPath\(2, 'college', 1, this\)/);
assert.doesNotMatch(html, /<details[^>]*\bopen\b/);
html = render('programLinks(item, 2, "tesda")', {tesda_options:[{name:'Caregiving NC II'},{name:'Health Care Services NC II'}]});
assert.match(html, /Show 1 more TESDA qualifications/);
html = render('renderFitEvidence(item)', {fit_evidence:[{task:'Analyze samples.', connections:['Investigation · 5/5']}]});
assert.match(html, /Analyze samples/);
assert.doesNotMatch(html, /Investigation · 5\/5/);
assert.doesNotMatch(html, /aligns with/);
html = render('renderFitEvidence(item)', {fit_evidence:[{task:'<script>alert(1)</script>', connections:['<b>unsafe</b>']}]});
assert.doesNotMatch(html, /<script>|<b>/);
assert.match(html, /&lt;script&gt;/);
assert.match(render('programLinks(item, 1, "tesda")', {tesda_options:[{name:'Web Development NC III',source_url:'https://www.tesda.gov.ph/download'}]}), /followStudyPath\(1, 'tesda', 0, this\)/);
assert.doesNotMatch(render('renderFitEvidence(item)', {fit_evidence:[{task:'Develop software.',explanation:'This work may suit you if you enjoy solving problems.'}]}), /solving problems/);
console.log('PASS: salary visible, qualifications preserved, sources collapsed, missing pay, single/multiple study paths, evidence and escaping.');
// Exercise the complete card renderer, including accessible disclosure toggling.
const grid={innerHTML:''};
context.document={getElementById:id=>id==='result-grid'?grid:null};
context.card={title:'Web Developers',code:'15-1254.00',salary:'PHP 30,000–50,000 / month',salary_reference:{measure:'advertised_p25_p75',match_type:'exact',median:40000,year:'2026',reviewed_on:'2026-10-31'},college_options:[{name:'Bachelor of Science in Information Technology',source_url:'https://region3.ched.gov.ph/resources/program-registry'}],tesda_options:[{name:'Web Development NC III',source_url:'https://www.tesda.gov.ph/download'}],wfh_info:'Remote or hybrid work may be possible. Coding can be handled online.',onet_url:'https://www.onetonline.org/link/summary/15-1254.00',fit_evidence:[{task:'Develop websites.',explanation:'This part of the role may suit you if you enjoy solving problems.'}]};
vm.runInContext('allRecommendations=[card]; currentPage=1; itemsPerPage=6; selectedGoal="Continue to College / Higher Ed"; renderPaginationControls=()=>{}; renderPaginatedResults();',context);
assert.match(grid.innerHTML,/Web Development NC III/);
assert.match(grid.innerHTML,/Find schools/);
assert.match(grid.innerHTML,/Find training/);
assert.match(grid.innerHTML,/PHP 40,000/);
assert.ok(grid.innerHTML.indexOf('College study paths') < grid.innerHTML.indexOf('TESDA qualifications'));
assert.ok(grid.innerHTML.indexOf('TESDA qualifications') < grid.innerHTML.indexOf('Salary reference'));
assert.ok(grid.innerHTML.indexOf('Work arrangement') > grid.innerHTML.indexOf('id="details-0"'));
assert.match(grid.innerHTML,/class="action-plan-btn"[^>]*followStudyPath\(0, 'college', 0, this\)/);
assert.match(grid.innerHTML,/Source last checked: 2026-10-31/);
assert.match(grid.innerHTML,/id="details-0"[^>]*hidden/);
assert.equal((grid.innerHTML.match(/Work arrangement/g)||[]).length,1);
assert.doesNotMatch(grid.innerHTML,/Remote work setup|feature-pill|Study paths are related options|5\/5/);
const content={hidden:true};let expanded;
context.document={getElementById:()=>content};
context.event={preventDefault(){},stopPropagation(){},currentTarget:{setAttribute:(name,value)=>{expanded=value;}}};
vm.runInContext('toggleDetails(event,"details-0")',context);
assert.equal(content.hidden,false);assert.equal(expanded,'true');
vm.runInContext('toggleDetails(event,"details-0")',context);
assert.equal(content.hidden,true);assert.equal(expanded,'false');
console.log('PASS: full card rendering, real education links, median/source dates, single work-arrangement section, and accessible expand/collapse.');

const area={hidden:true};let isExpanded='false';
context.document={getElementById:()=>area};
context.programButton={getAttribute:name=>name==='aria-controls'?'program-options-2-college':isExpanded,setAttribute:(name,value)=>{if(name==='aria-expanded')isExpanded=value;}};
vm.runInContext('toggleProgramOptions(programButton)',context);
assert.equal(area.hidden,false);assert.equal(isExpanded,'true');
vm.runInContext('toggleProgramOptions(programButton)',context);
assert.equal(area.hidden,true);assert.equal(isExpanded,'false');
html=render('programLinks(item,2,"college")',{college_options:[{name:'Hospitality Management',source_url:'https://ro11.ched.gov.ph/programs-per-hei/'},{name:'Tourism Management'}]});
assert.match(html, /class="career-program-link"[^>]*>Hospitality Management<span class="career-program-link-arrow"/);
assert.ok(html.indexOf('career-program-controls') > html.indexOf('career-program-link-arrow'));
console.log('PASS: program-name arrow, links below names, collapsed alternatives, modest salary below TESDA, and work details collapsed.');

for (const [goal, expected] of [
  ['Continue to College / Higher Ed', /Find colleges/],
  ['Vocational Certification (Tech-Voc)', /Find training/],
  ['Immediate Workforce Entry', /href="https:\/\/ph.jobstreet.com\/web-developers-jobs"/],
  ['Work From Home / Home Caregiver', /href="https:\/\/www.onlinejobs.ph\/jobseekers\/jobsearch\?jobkeyword=Web\+Developers/ ],
]) {
  context.goal=goal;
  const action=vm.runInContext('renderCareerAction(card, 0, goal)',context);
  assert.match(action,expected);
  assert.match(action,/action-plan-btn/);
}
console.log('PASS: restored primary college, TESDA, Jobstreet, and remote job buttons.');

// Search parameters must be taken from this card, never a fixed/sample career.
for (const title of ['Web Developers', 'Graphic Designers', 'Bookkeeping, Accounting, and Auditing Clerks', 'Writer & Editor']) {
  context.title=title;
  const action=vm.runInContext('getActionPlanInfo("Work From Home / Home Caregiver", title)',context);
  const url=new URL(action.url);
  assert.equal(url.pathname,'/jobseekers/jobsearch');
  assert.equal(url.searchParams.get('jobkeyword'),title);
  assert.equal(url.searchParams.has('keyword'),false);
  for (const key of ['fullTime','partTime','gig']) assert.equal(url.searchParams.get(key),'on');
  assert.equal(action.label,'Find remote jobs');
}
html=render('programLinks(item, 3, "college")',{college_options:[{name:'Nursing',source_url:'https://example.org/source'}]});
assert.doesNotMatch(html,/Near me|>Program source|>Qualification/);
assert.match(html,/career-program-link/);
assert.doesNotMatch(html,/career-study-action/);
assert.match(html,/career-source-button/);
assert.match(html,/aria-label="Program information for Nursing"/);
assert.match(html,/followStudyPath\(3, 'college', 0, this\)/);
assert.doesNotMatch(grid.innerHTML,/A closer look/);
context.kind='tesda';
const trainingUrl=new URL(vm.runInContext('studySearchUrl(kind, "Cookery NC II", "Laguna")',context));
assert.equal(trainingUrl.searchParams.get('SearchCourse'),'Cookery NC II');
assert.equal(trainingUrl.searchParams.get('SearchLoc'),'Laguna');
const salaryMarkup=render('renderSalaryReference(item)',item);
assert.match(salaryMarkup,/career-salary-text/);
assert.match(salaryMarkup,/career-salary-chevron/);
assert.doesNotMatch(salaryMarkup,/career-salary-value[^>]*>[^<]*⌄/);
console.log('PASS: compact study controls, removed eyebrow, separate salary chevron, and career-specific remote searches with the correct query field.');

// A focus/hover preview must survive the first touch activation, then close on the next.
const home={append(panel){panel.parentNode=this;}};
const popup={id:'source-test',hidden:true,style:{},parentNode:home,open:false,
  matches(selector){return selector===':popover-open' && this.open;},
  showPopover(){this.open=true;},hidePopover(){this.open=false;},
  getBoundingClientRect(){return {height:140};}};
let sourceExpanded='false';
const sourceButton={getAttribute(){return 'source-test';},setAttribute(name,value){if(name==='aria-expanded')sourceExpanded=value;},getBoundingClientRect(){return {left:290,top:570,bottom:600};}};
context.document={getElementById:()=>popup,body:{append(panel){panel.parentNode=this;}}};
context.window={innerWidth:320,innerHeight:640};
context.sourceButton=sourceButton;
vm.runInContext('openProgramSource(sourceButton)',context);
assert.equal(popup.open,true);assert.equal(sourceExpanded,'true');
assert.ok(parseFloat(popup.style.left)>=12);
assert.ok(parseFloat(popup.style.left)+parseFloat(popup.style.width)<=308);
assert.ok(parseFloat(popup.style.top)+140<=628);
vm.runInContext('toggleProgramSource(sourceButton)',context);
assert.equal(popup.open,true);assert.equal(popup.hidden,false);
vm.runInContext('toggleProgramSource(sourceButton)',context);
assert.equal(popup.open,false);assert.equal(popup.hidden,true);assert.equal(sourceExpanded,'false');
// Native light dismissal clears the button's expanded state.
vm.runInContext('openProgramSource(sourceButton)',context);popup.open=false;
context.toggleEvent={newState:'closed',target:popup};
vm.runInContext('syncProgramSource(toggleEvent)',context);
assert.equal(sourceExpanded,'false');
// Older browsers use the same tap behavior with a fixed-position fallback.
popup.showPopover=undefined;popup.hidePopover=undefined;
vm.runInContext('openProgramSource(sourceButton); toggleProgramSource(sourceButton)',context);
assert.equal(popup.hidden,false);assert.equal(popup.parentNode,context.document.body);
vm.runInContext('closeProgramSource()',context);
assert.equal(popup.hidden,true);assert.equal(popup.parentNode,home);
console.log('PASS: hover/focus preview, first-tap pinning, second-tap dismissal, native close synchronization, viewport placement, and older-browser fallback.');

// The program name itself is the nearby search action, with no duplicate search row.
context.localStorage={getItem:()=>JSON.stringify({name:'Laguna'})};
for (const [kind, name] of [['college','Bachelor of Science in Mechanical Engineering'],['tesda','Mechanical Drafting NC I']]) {
  context.kind=kind;
  const value=kind==='college'?{college_options:[{name}]}:{tesda_options:[{name}]};
  const markup=render('programLinks(item,0,kind)',value);
  assert.match(markup,/class="career-program-link"/);
  assert.match(markup,/career-program-link-arrow/);
  assert.doesNotMatch(markup,/career-study-action/);
  const href=markup.match(/class="career-program-link" href="([^"]+)"/)[1].replaceAll('&amp;','&');
  const url=new URL(href);
  if (kind==='college') {
    assert.match(url.searchParams.get('q'),/Mechanical Engineering/);
    assert.match(url.searchParams.get('q'),/Laguna/);
  } else {
    assert.equal(url.searchParams.get('SearchCourse'),name);
    assert.equal(url.searchParams.get('SearchLoc'),'Laguna');
  }
}
let opened=[];
context.window={open:url=>opened.push(url)};
vm.runInContext('followStudyPath(0,"college",0)',context);
vm.runInContext('followStudyPath(0,"tesda",0)',context);
assert.match(new URL(opened[0]).searchParams.get('q'),/Information Technology.*Laguna/);
assert.equal(new URL(opened[1]).searchParams.get('SearchCourse'),'Web Development NC III');
assert.equal(new URL(opened[1]).searchParams.get('SearchLoc'),'Laguna');
console.log('PASS: linked program/qualification names, inline arrow, no duplicate search action, and selected-program nearby destinations.');

assert.match(grid.innerHTML,/What this career involves/);
assert.doesNotMatch(grid.innerHTML,/Why This May Suit You|Why it may fit|may suit you if/);
assert.match(grid.innerHTML,/Read the O\*NET career profile/);
html=render('renderFitEvidence(item)',{description:'Maintain records.',fit_reasons:['You are naturally gifted.']});
assert.match(html,/Maintain records/);assert.doesNotMatch(html,/naturally gifted/);
console.log('PASS: O*NET description only; no cached fit templates or unsupported personal-fit claims rendered.');
(async()=>{
  let stored=null, openedTabs=[], notices=[];
  const locationLabel={textContent:''};
  const fallbackLink={dataset:{studyKind:'college',studyProgram:'Bachelor of Science in Information Technology'},href:''};
  context.localStorage={getItem:()=>stored,setItem:(key,value)=>{stored=value;}};
  context.document={getElementById:id=>id==='study-search-location-value'?locationLabel:null,querySelectorAll:()=>[fallbackLink]};
  context.showToast=message=>notices.push(message);
  function newTab(){return {opener:{},closed:false,replaced:'',location:{replace(url){this.owner.replaced=url;}},close(){this.closed=true;}};}
  context.window={open:(url,target)=>{const tab=newTab();tab.location.owner=tab;openedTabs.push({url,target,tab});return tab;},location:{assign(){throw new Error('The assessment page must remain open.');}}};
  vm.runInContext('requestStudyLocation=async()=>{rememberStudyLocation("Cavite");return "Cavite";}',context);
  await vm.runInContext('followStudyPath(0,"college",0)',context);
  assert.equal(openedTabs[0].url,'about:blank');
  assert.equal(openedTabs[0].tab.opener,null);
  assert.match(new URL(openedTabs[0].tab.replaced).searchParams.get('q'),/Information Technology.*Cavite/);
  assert.equal(locationLabel.textContent,'Cavite');
  assert.match(new URL(fallbackLink.href).searchParams.get('q'),/Cavite/);
  assert.equal(openedTabs[0].tab.closed,false);
  stored=null;
  vm.runInContext('requestStudyLocation=async()=>null;',context);
  await vm.runInContext('followStudyPath(0,"tesda",0)',context);
  assert.equal(openedTabs[1].tab.closed,true);
  stored=null;
  context.window.open=()=>null;
  vm.runInContext('requestStudyLocation=async()=>{rememberStudyLocation("Laguna");return "Laguna";}',context);
  await vm.runInContext('followStudyPath(0,"tesda",0)',context);
  assert.match(notices.at(-1),/Select the program again/);
  assert.equal(locationLabel.textContent,'Laguna');
  let promptDefault;
  context.window.prompt=(message,initial)=>{promptDefault=initial;return 'Calamba, Laguna';};
  vm.runInContext('changeStudyLocation()',context);
  assert.equal(promptDefault,'Laguna');
  assert.equal(locationLabel.textContent,'Calamba, Laguna');
  assert.match(new URL(fallbackLink.href).searchParams.get('q'),/Calamba, Laguna/);
  console.log('PASS: editable search area, fresh fallback URLs, asynchronous search tab, cancellation cleanup, and blocked-popup recovery without replacing the assessment.');
})().catch(error=>{console.error(error);process.exitCode=1;});
