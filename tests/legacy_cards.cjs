// Focused regression for the preserved card and the new search boundary.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const nodes = new Map(), opened = [], storage = new Map();
function el(id) {
  if (!nodes.has(id)) nodes.set(id, {innerHTML:'', value:'', textContent:'', children:[], listeners:{}, isConnected:true,
    addEventListener(type, callback) {this.listeners[type]=callback;},
    append(option) {this.children.push(option);if(this.children.length===1)this.value=option.value;},
    replaceChildren() {this.children=[];this.value='';}, showModal() {this.open=true;}, close() {this.open=false;this.listeners.close?.();}, focus() {}, after() {}});
  return nodes.get(id);
}
const s={console,URL,URLSearchParams, setTimeout,clearTimeout, navigator:{},
 document:{getElementById:el,createElement:()=>({})},
 localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},
 window:{open:(...args)=>opened.push(args),isSecureContext:false},
 postFeedback:()=>Promise.resolve(),showToast(){},
 selectedGoal:'Continue to College / Higher Ed', currentPage:1,itemsPerPage:6,
 goalOptions:[{goal:'Continue to College / Higher Ed',label:'College'}],
 allRecommendations:[{title:'Mechanical Engineers', code:'17-2141.00',college_majors:'Program One | Program Two',tech_voc:'Qualification One | Qualification Two',fit_reasons:['Original reason'],description:'Original description',onet_url:'https://www.onetonline.org/',salary:'PHP 20,000–30,000 / month',salary_reference:{source_name:'Jobstreet PH',measure:'advertised_p25_p75',source_url:'https://ph.jobstreet.com/career-advice/role/engineer/salary',source_occupation:'Engineer',match_type:'related',reviewed_on:'2026-10-31'}}]};
vm.createContext(s);
for(const file of ['api-client.js','career-results.js','program-search.js'])vm.runInContext(fs.readFileSync('app/static/js/'+file,'utf8'),s);
s.postFeedback=()=>Promise.resolve();
const run=code=>vm.runInContext(code,s);
run('renderPaginatedResults()');
const html=el('result-grid').innerHTML;
for(const text of ['pathway-metrics-box','Career Details & Next Steps','Why This May Suit You','Original reason','Program One; Program Two','Qualification One; Qualification Two','Jobstreet reference'])assert.ok(html.includes(text),text);
assert.ok(!html.includes('career-program-link'));
assert.ok(!html.includes('What this career involves'));
run('handleCareerSearch({preventDefault() {}}, 0, null)');
assert.equal(el('study-search-dialog').open,true); assert.equal(opened.length,0);
assert.equal(el('study-program').children.length,2);
el('study-program').value='Program Two';el('study-area').value='Calamba, Laguna';
el('study-search-form').listeners.submit({preventDefault(){}});
let url=new URL(opened[0][0]);assert.equal(url.hostname,'www.google.com');assert.ok(url.searchParams.get('q').includes('Program Two schools in Calamba, Laguna'));
run('openStudySearch(0, "tesda", null)');assert.equal(el('study-search-dialog').open,true);assert.equal(opened.length,1);
el('study-program').value='Qualification Two';el('study-area').value='Laguna';el('study-search-form').listeners.submit({preventDefault(){}});
url=new URL(opened[1][0]);assert.equal(url.hostname,'www.tesda.gov.ph');assert.equal(url.searchParams.get('SearchCourse'),'Qualification Two');assert.equal(url.searchParams.get('SearchLoc'),'Laguna');
assert.ok(run('jobstreetSalary({salary:"PHP 1–999", salary_reference:{source_name:"PSA"}})').includes('No matched Jobstreet'));
assert.ok(!run('jobstreetSalary({salary:"PHP 1–999", salary_reference:{}})').includes('999'));
assert.equal(new URL(run('getActionPlanInfo("Work From Home", "Graphic Designer").url')).href, 'https://ph.jobstreet.com/remote-graphic-designer-jobs');
assert.equal(new URL(run('getActionPlanInfo("Immediate Workforce Entry", "Mechanical Engineers").url')).pathname,'/Mechanical-Engineers-jobs');
const salary = run('jobstreetSalary({...allRecommendations[0],salary:"PHP 20,000–30,000 / month (middle 50% of advertised pay; 2026)"})');
assert.ok(salary.startsWith('PHP 20,000–30,000 / month <a'));
assert.ok(!salary.replace(/<[^>]+>/g, '').includes('related role'));
assert.ok(!salary.includes('middle 50%'));
console.log('PASS: legacy card labels, plain program lists, salary provenance, modal-first search, selected program/location destinations and job URLs.');
