const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const links=[],toasts=[],revoked=[];let request,resolveRequest;
const span={textContent:'Download PDF'};
const button={disabled:false,attrs:{},querySelector:()=>span,setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};
const s={AbortController,console,completedSubmissionId:'saved_submission_123',allRecommendations:Array.from({length:30},()=>({})),
 setTimeout:()=>1,clearTimeout(){},showToast:m=>toasts.push(m),URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:u=>revoked.push(u)},
 document:{body:{appendChild:l=>links.push(l)},createElement:()=>({click(){this.clicked=true;},remove(){this.removed=true;}})},
 apiFetch:async(url,options)=>{request={url,options};return{headers:{get:()=> 'application/pdf'},blob:async()=>({})};}};
vm.createContext(s);vm.runInContext(fs.readFileSync('app/static/js/career-pdf.js','utf8'),s);s.button=button;
const run=code=>vm.runInContext(code,s);
(async()=>{
 await run('downloadCareerPDF(button)');
 assert.equal(request.url,'/api/career-report');assert.deepEqual(JSON.parse(request.options.body),{submission_id:'saved_submission_123'});
 assert.equal(links.length,1);assert.equal(links[0].download,'ALS-Gabay-Career-Cards.pdf');assert.ok(links[0].clicked&&links[0].removed);
 assert.equal(button.disabled,false);assert.equal(span.textContent,'Download PDF');
 s.apiFetch=()=>new Promise(resolve=>{resolveRequest=resolve;});
 const pending=run('downloadCareerPDF(button)');await run('downloadCareerPDF(button)');assert.equal(button.disabled,true);
 resolveRequest({headers:{get:()=> 'application/pdf'},blob:async()=>({})});await pending;assert.equal(links.length,2);
 s.apiFetch=async()=>{throw new Error('Network unavailable');};await run('downloadCareerPDF(button)');assert.equal(toasts.at(-1),'Network unavailable');assert.equal(button.disabled,false);
 s.apiFetch=async()=>({headers:{get:()=> 'text/html'}});await run('downloadCareerPDF(button)');assert.equal(links.length,2);
 s.completedSubmissionId=null;await run('downloadCareerPDF(button)');assert.match(toasts.at(-1),/Complete your assessment/);
 console.log('PASS: PDF download, saved submission only, duplicate guard, error recovery, response validation and missing assessment.');
})().catch(e=>{console.error(e);process.exitCode=1;});
