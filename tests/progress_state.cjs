// Dependency-free state regression: fresh JS contexts share only localStorage.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const storage=new Map();
function boot({blocked=false,hash=''}={}) {
 const nodes=new Map(),events={};
 function el(id) {
  if(!nodes.has(id))nodes.set(id,{id,hidden:id==='results'||id==='page-quiz',style:{},disabled:false,open:false,shows:0,
   innerHTML:'',textContent:'',dataset:{},listeners:{},classList:{add(){},remove(){}},
   appendChild(){},remove(){},querySelector(){return el(id+' span');},querySelectorAll(){return[];},
   setAttribute(){},focus(){},getBoundingClientRect(){return{top:0,height:60};},
   addEventListener(type,callback){this.listeners[type]=callback;},
   close(){this.open=false;},showModal(){this.open=true;this.shows++;},after(){}});
  return nodes.get(id);
 }
 el('assessment-questions').textContent=fs.readFileSync('data/reference/assessment_questions.json','utf8');
 const location={hash,pathname:'/',search:''};
 const s={console,AbortController,setTimeout,clearTimeout,TypeError,location,
  history:{replaceState(){location.hash='';},pushState(){}},performance:{getEntriesByType(){return[{type:'reload'}];}},
  document:{getElementById:el,createElement:()=>el('toast'),querySelector:()=>({content:'session_for_progress',focus(){},getBoundingClientRect(){return{height:60};}}),
   documentElement:{dataset:{}},addEventListener(type,callback){events['document-'+type]=callback;}},
  window:{scrollY:600,matchMedia:()=>({matches:false}),scrollTo({top}){this.scrollY=top;},addEventListener(type,callback){events[type]=callback;}},
  localStorage:{getItem:k=>storage.get(k)||null,setItem(k,v){if(blocked)throw new Error('Storage blocked');storage.set(k,v);},removeItem:k=>storage.delete(k)},
  crypto:{getRandomValues(bytes){bytes.fill(7);return bytes;}},Headers,
 };
 vm.createContext(s);
 for(const file of ['api-client.js','assessment-options.js','assessment.js','career-results.js','page-navigation.js','assessment-progress.js'])vm.runInContext(fs.readFileSync('app/static/js/'+file,'utf8'),s);
 vm.runInContext('postFeedback=async()=>({});renderPaginatedResults=()=>{};',s);
 return {s,el,events,run:code=>vm.runInContext(code,s)};
}
(async()=>{
 let p=boot();p.run('navigate("quiz");selectGoal("Continue to College / Higher Ed");changeStep(1);selectEdu("Elementary Level");changeStep(1);handleAnswerSelect("R1",4);');
 let d=JSON.parse(storage.get('gabay.assessment-progress.v1'));
 assert.equal(d.step,3);assert.equal(d.answers.R1,4);
 p=boot({hash:'#about-platform'});assert.equal(p.el('assessment-resume-modal').open,true);assert.equal(p.run('Object.keys(answers).length'),0);
 assert.equal(p.s.location.hash,'');assert.equal(p.s.window.scrollY,0);
 p.run('continueSavedAssessment()');assert.equal(p.run('answers.R1'),4);assert.equal(p.run('currentStep'),3);assert.equal(p.run('selectedEducation'),'Elementary Level');assert.equal(p.run('selectedGoal'),'Continue to College / Higher Ed');
 p.run('currentStep=4;answers=Object.fromEntries(questionsData.map(q=>[q.id,3]));toggleSkill("Programming and coding");');
 p.s.apiFetch=async()=>{throw new TypeError('Offline');};await p.run('submitAssessment()');
 assert.equal(p.el('assessment-error-modal').open,true);
 const token=p.run('pendingSubmission.id');
 p=boot();assert.equal(p.el('assessment-resume-modal').open,true);p.run('continueSavedAssessment()');
 assert.equal(p.run('currentStep'),4);assert.equal(p.run('pendingSubmission.id'),token);assert.equal(p.run('selectedSkills[0]'),'Programming and coding');
 p.s.apiFetch=async()=>({json:async()=>({status:'success',recommendations:[]})});await p.run('submitAssessment()');
 assert.equal(storage.has('gabay.assessment-progress.v1'),false);p.run('clearTimeout(dwellTimer)');
 p=boot();assert.equal(p.el('assessment-resume-modal').open,false);
 p.run('navigate("quiz");selectEdu("Elementary Level");');p=boot();p.run('retakeSavedAssessment()');
 assert.equal(p.run('currentStep'),1);assert.equal(p.run('selectedEducation'),'Junior High School');assert.equal(p.run('Object.keys(answers).length'),0);
 p=boot();assert.equal(p.el('assessment-resume-modal').open,true);p.el('assessment-resume-modal').close();
 p.run('navigate("quiz")');assert.equal(p.el('assessment-resume-modal').open,true); // Escape does not erase saved inputs.
 storage.set('gabay.assessment-progress.v1','{broken');p=boot();assert.equal(p.el('assessment-resume-modal').open,false);
 storage.set('gabay.assessment-progress.v1',JSON.stringify({...d,goal:'invalid'}));p=boot();assert.equal(p.el('assessment-resume-modal').open,false);
 storage.clear();p=boot({blocked:true});p.run('navigate("quiz");changeStep(1);');assert.equal(p.run('currentStep'),2);assert.equal(p.run('assessmentStorageWarningShown'),true);
 console.log('PASS: reload recovery, original choices and skills, offline retry identity, completion cleanup, retake, cancel/reopen, invalid/blocked storage and hero scroll reset.');
})().catch(error=>{console.error(error);process.exitCode=1;});
