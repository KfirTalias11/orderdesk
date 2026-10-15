const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const vm = require('node:vm');

function element() {
  return {value:'',disabled:false,hidden:true,textContent:'',children:[],listeners:{},
    append(...nodes){this.children.push(...nodes);},
    replaceChildren(...nodes){this.children=nodes;},
    addEventListener(name,fn){this.listeners[name]=fn;}};
}

test('polling cannot allow a second order while submission is pending', async () => {
  const elements = new Map();
  const get = id => {if(!elements.has(id))elements.set(id,element());return elements.get(id);};
  get('product').value='1';get('quantity').value='1';get('customer').value='Studio';get('filter').value='all';
  let posts=0,tick;
  const context={document:{getElementById:get,createElement:element},Intl,Date,AbortSignal,
    setInterval(fn){tick=fn;},
    async fetch(url,options){
      if(options.method==='POST'){posts++;return new Promise(()=>{});}
      const body=url.endsWith('/products')?[{id:1,name:'Notebook',price_cents:2400}]:url.endsWith('/orders')?[]:
        {dependencies:{postgres:'available',redis:'available'},worker:{state:'running'},summary:{orders:0,pending:0,revenue_cents:0}};
      return {ok:true,json:async()=>body};
    }};
  vm.runInNewContext(readFileSync('web/app.js','utf8'),context);
  await new Promise(setImmediate);
  const submit=get('order-form').listeners.submit;
  submit({preventDefault(){}});
  assert.equal(get('submit').disabled,true);
  await tick();
  assert.equal(get('submit').disabled,true,'polling must preserve the submission lock');
  submit({preventDefault(){}});
  assert.equal(posts,1,'repeated submit events must not create duplicate requests');
});
