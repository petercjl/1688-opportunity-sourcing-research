import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {ROOT} from '../src/core.mjs';
import {execute,discoverPython} from '../src/runtime.mjs';
const py=await discoverPython({imports:[]});
const env={...process.env,PYTHONUTF8:'1',PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1'};
for(const script of ['test_search_expansion.py','test_remote_image_flow.py','test_build_output_image_validation.py'])test(script,async()=>{
 assert(py.available,'Python 3 required');await execute(py.command,[...py.args,path.join(ROOT,'skill/tests',script)],{env,encoding:'utf8',timeout:30000});
});
test('normalized capability to collection to evidence preserves UTF-8 and facts, and reports service failure',async()=>{
 const temp=await fs.mkdtemp(path.join(os.tmpdir(),'1688-contract-'));
 try{
 const stub=path.join(temp,'atomic.mjs');
 await fs.writeFile(stub,`const [group,action,query]=process.argv.slice(2);
 if(group==='capabilities')console.log(JSON.stringify({contracts:{products:'1688-products@1',suppliers:'1688-suppliers@1'}}));
 else if(group==='doctor')console.log(JSON.stringify({ok:true,product_skill:{available:true},supplier_skill:{available:true},python:{available:true},ak:{available:true}}));
 else if(process.env.TEST_QUERY_FAILURE){console.error(JSON.stringify({ok:false,error:{code:'AUTH_REQUIRED',message:'expired'}}));process.exitCode=1;}
 else if(group==='products')console.log(JSON.stringify({ok:true,kind:'products',query,products:[{offer_id:'1',title:'中文锅',url:'https://example.com/offer',image_url:'https://example.com/image.jpg',price:12,moq:3,stock_amount:42,supplier_name:'测试商家',promotion_tags:['标签']}]}));
 else console.log(JSON.stringify({ok:true,kind:'suppliers',query,suppliers:[{company_name:'中文工厂',url:'https://example.com/factory',factory_types:['源头'],supports_proofing:true,monthly_orders:12}]}));`);
 const categories=['market_proven','novel_structure','aesthetic','scenario_specific','premium_quality','solution_bundle'];
 const plan={handoff_type:'ai_dianjing_to_1688_product_selection',execution_policy:{mode:'read_only_research'},opportunities:[{opportunity_id:'op-1',search_tasks:[...categories.map((c,i)=>({task_id:'task-'+i,capability:'1688-product-find.text_search',query:'中文查询 '+c,strategy_category:c,search_direction:c,search_round:1})),{task_id:'supplier-1',capability:'1688-source-suppliers',query:'中文工厂',strategy_category:'supplier_baseline'}]}]};
 const input=path.join(temp,'plan.json');await fs.writeFile(input,JSON.stringify(plan));
 const run=(script,args,extra={})=>execute(process.execPath,[path.join(ROOT,'scripts/1688-opportunity-sourcing-research.mjs'),'script',script,...args],{env:{...env,ALI1688_CLI_ENTRY:stub,...extra},encoding:'utf8',timeout:60000});
 const out=path.join(temp,'collection');await run('collect_results.py',['--input',input,'--output-dir',out]);
 const evidence=path.join(temp,'evidence.json');await run('prepare_evidence.py',['--collection',path.join(out,'collection.json'),'--output',evidence]);
 const result=JSON.parse(await fs.readFile(evidence,'utf8')).opportunities[0];
 assert.equal(result.products.length,1);assert.equal(result.products[0].title,'中文锅');assert.equal(result.products[0].stock_amount,42);assert.equal(result.products[0].quantity_begin,3);assert.equal(result.products[0].provenance.length,6);assert.equal(result.suppliers[0].support_proofing,true);
 const failed=path.join(temp,'failed');await assert.rejects(run('collect_results.py',['--input',input,'--output-dir',failed],{TEST_QUERY_FAILURE:'1'}));
 const collection=JSON.parse(await fs.readFile(path.join(failed,'collection.json'),'utf8'));assert.equal(collection.success_count,0);assert.equal(collection.failure_count,7);
 const raw=JSON.parse(await fs.readFile(path.join(failed,'raw-results/task-0.json'),'utf8'));assert.equal(raw.error.code,'AUTH_REQUIRED');
 }finally{await fs.rm(temp,{recursive:true,force:true});}
});
