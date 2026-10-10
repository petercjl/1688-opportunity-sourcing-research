import { dependencyHealth, toolRun } from './dependencies.mjs';
import { discoverPython, execute } from './runtime.mjs';
import { atomicEntry } from './dependencies.mjs';
import { ROOT } from './core.mjs';
import { META, AGENTS } from './core.mjs';
import { readFile, open } from 'node:fs/promises';
import { resolve } from 'node:path';
import { capabilities } from './capabilities.mjs';
import { CliError, failure } from './errors.mjs';
import { installSkill, skillSource, skillStatus, updateSkill } from './skill-manager.mjs';
import { packageUpdate } from './updater.mjs';

const usage = `1688-opportunity-sourcing-research — 六类机会选品应用
script <build_search_plan.py|collect_results.py|prepare_evidence.py|prepare_image_review.py|build_outputs.py|discover_runtime.py> [arguments...]
tool <1688cli arguments...>
version | capabilities | doctor | skill source|status|install|update | update check|install`;

const optionNames = new Set(['limit', 'sort', 'score-level', 'purchase-amount', 'tags', 'ic-tags', 'image', 'output', 'output-dir', 'tag-dir', 'context', 'max-price', 'max-moq', 'min-sold', 'location', 'relevance', 'category', 'supplier', 'agent', 'path', 'mode']);
const flags = new Set(['json', 'proofing', 'check', 'apply', 'help', 'version', 'force']);

export function parseArgs(argv) {
  const positionals = [];
  const options = {};
  for (let i = 0; i < argv.length; i++) {
    const item = argv[i];
    if (!item.startsWith('--')) { positionals.push(item); continue; }
    const name = item.slice(2);
    if (flags.has(name)) { options[name] = true; continue; }
    if (!optionNames.has(name)) throw new CliError('INVALID_OPTION', `未知选项：${item}`);
    if (!argv[i + 1] || argv[i + 1].startsWith('--')) throw new CliError('MISSING_OPTION_VALUE', `选项 ${item} 缺少值`);
    options[name] = argv[++i];
  }
  return { positionals, options };
}

function required(value, label) {
  if (!value || value.startsWith('--')) throw new CliError('MISSING_INPUT', `缺少${label}`);
  return value;
}

async function runCommand(positionals, options) {
  const [group, action, input] = positionals;
  if (group === 'version' || options.version) return { version: META.version };
  if (!group || group === 'help' || options.help) return { help: usage };
  if (group === 'capabilities') return { ok: true, package: META.name, version: META.version, agents: AGENTS, operating_systems: ['darwin','win32'], capabilities, lifecycle: ['skill source','skill status','skill install','skill update','update check','update install'], dependencies: ['@petercjl/1688cli >=0.4 <1: 1688-products@1 / 1688-suppliers@1','Python 3 standard library'], layer:'application' };
  if (group === 'doctor') { const dependency=await dependencyHealth(); const python=await discoverPython({imports:[]}); return {ok:dependency.ok&&python.available,package:META.name,version:META.version,layer:'application',dependency,python,skill:await skillStatus()}; }
  if (group === 'update') {
    if(action && !['check','install'].includes(action)) throw new CliError('UNKNOWN_COMMAND','update 支持 check、install');
    return packageUpdate(Boolean(options.apply || action==='install'));
  }
  if (group === 'skill') {
    if (action === 'source') return { ok: true, source: skillSource() };
    if (action === 'status') return { ok: true, ...(await skillStatus({agent:options.agent,path:options.path})) };
    if (!['install', 'update'].includes(action)) throw new CliError('UNKNOWN_COMMAND', 'skill 支持 source、status、install、update');
    const agents = options.agent === 'all' ? AGENTS : [options.agent || 'codex'];
    if(options.path && agents.length>1) throw new CliError('INVALID_INPUT','--path 须指定单个 Agent');
    const opts={path:options.path,mode:options.mode,force:options.force};
    const results = [];
    for (const agent of agents) results.push(action === 'install' ? await installSkill(agent,opts) : await updateSkill(agent,opts));
    return { ok: true, results };
  }
  throw new CliError('UNKNOWN_COMMAND', '未知命令；运行 1688-opportunity-sourcing-research help 查看用法');
}

async function saveNew(path, content) {
  let handle;
  try {
    handle = await open(resolve(path), 'wx', 0o600);
    await handle.writeFile(content);
  } catch (error) {
    if (error.code === 'EEXIST') throw new CliError('OUTPUT_EXISTS', '输出文件已存在，拒绝覆盖', { path: resolve(path) });
    throw error;
  } finally { await handle?.close(); }
}

export async function main(argv, io = console) {
  try {
    if (argv[0] === 'script') {
      const allowed=['build_search_plan.py','collect_results.py','prepare_evidence.py','prepare_image_review.py','build_outputs.py','discover_runtime.py'];
      if(!allowed.includes(argv[1]))throw new CliError('SCRIPT_NOT_ALLOWED','Unknown application script');
      const python=await discoverPython({imports:[]});if(!python.available)throw new CliError('PYTHON_MISSING','Install Python 3');
      const env={...process.env,PYTHONUTF8:'1',PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1',ALI1688_NODE:process.execPath};
      if(['collect_results.py','discover_runtime.py'].includes(argv[1])) env.ALI1688_CLI_ENTRY=await atomicEntry();
      try {const r=await execute(python.command,[...python.args,resolve(ROOT,'skill/scripts',argv[1]),...argv.slice(2)],{env,encoding:'utf8',timeout:1800000,maxBuffer:32*1024*1024});if(r.stdout.trim())io.log(r.stdout.trim());return 0;}
      catch(e){throw new CliError('SCRIPT_FAILED','Application script failed',{script:argv[1],reason:e.stderr?.slice(0,2000)||e.code});}
    }
    if (argv[0] === 'tool') return toolRun(argv.slice(1),io);
    const { positionals, options } = parseArgs(argv);
    const result = await runCommand(positionals, options);
    const output = result.help || JSON.stringify(result, null, 2);
    if (options.output) await saveNew(options.output, `${output}\n`);
    io.log(output);
    return result.ok === false ? 1 : 0;
  } catch (error) {
    io.error(JSON.stringify(failure(error)));
    if (io === console) process.exitCode = 1;
    return 1;
  }
}
