const {strict: assert} = require('node:assert');
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const source = readFileSync(require('node:path').join(__dirname, '../static/game-recovery.js'), 'utf8');
async function check(status, body, expected, path='/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/command.php') {
    let removed=0, destination;
    const nodes=[];
    const host={replaceChildren(){removed++}, append(){}};
    const response=new Response(JSON.stringify(body),{status});
    const location={origin:'http://localhost:5050',href:'http://localhost:5050/ruffle.html',replace(url){destination=url}};
    const document={getElementById(){return host},createElement(tag){
        const element={tag,style:{},setAttribute(){},append(){},focus(){},addEventListener(_,fn){this.click=fn}};
        nodes.push(element);return element;
    }};
    const window={fetch:async()=>response};
    vm.runInNewContext(source,{window,location,document,URL,Request});
    const received=await window.fetch(location.origin+path);
    assert.equal(received,response); // Never rewrite a failure as success.
    assert.equal(removed,expected);
    if(expected){
        await window.fetch(location.origin+path);
        assert.equal(removed,1);
        nodes.find(n=>n.tag==='button').click();
        assert.equal(destination,'/ruffle.html?client=1.2.7');
    }
}
(async()=>{
    const error={code:'unsupported_action',recovery:'reload_saved_empire',result:'error'};
    await check(422,error,1);
    await check(200,{result:'success'},0);
    await check(422,{result:'error'},0);
    await check(422,error,0,'/other');
    console.log('Recovery response preservation, teardown, retry and reload tests PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
