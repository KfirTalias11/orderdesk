const $ = id => document.getElementById(id);
const money = cents => new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'}).format(cents/100);
let products = [], orders = [], busy = false;
async function api(path, options={}) {
  const response = await fetch('/api'+path, {...options, signal:AbortSignal.timeout(15000)});
  if (!response.ok) throw new Error(response.status >= 500 ? 'A service is unavailable. Check service status and try again.' : 'Please check the order details and try again.');
  return response.json();
}
function node(tag, text, className) { const el=document.createElement(tag); el.textContent=text; if(className) el.className=className; return el; }
function renderOrders() {
  const rows=orders.filter(order=>$('filter').value==='all'||order.status===$('filter').value);
  $('orders').replaceChildren();
  for(const order of rows) {
    const tr=document.createElement('tr');
    const customer=node('td',''); customer.append(node('strong',order.customer_name),node('small',`#OD-${String(order.id).padStart(4,'0')} · ${new Date(order.created_at).toLocaleDateString('en-US',{month:'short',day:'numeric'})}`));
    const product=node('td',order.product_name); product.append(node('small',`${order.sku} · Qty ${order.quantity}`));
    const status=node('td',''); status.append(node('span',order.status==='fulfilled'?'Fulfilled':'Pending',`badge ${order.status}`));
    tr.append(customer,product,node('td',money(order.total_cents),'amount'),status); $('orders').append(tr);
  }
  if(!rows.length){ const row=node('tr',''),cell=node('td','No orders here yet. Create an order to get started.','empty');cell.colSpan=4;row.append(cell);$('orders').append(row); }
}
function estimate(){ const product=products.find(p=>p.id===Number($('product').value)); $('estimate').textContent=product?money(product.price_cents*Number($('quantity').value||0)):'—'; }
function services(status){
  $('services').replaceChildren();
  const states=[['Order API','Available',true],['PostgreSQL',status.dependencies.postgres,status.dependencies.postgres==='available'],['Redis',status.dependencies.redis,status.dependencies.redis==='available'],['Fulfillment',status.worker.state,status.worker.state==='running']];
  states.forEach(([label,value,ok])=>{const row=node('li',label);row.append(node('span',value.charAt(0).toUpperCase()+value.slice(1),`service-state${ok?'':' bad'}`));$('services').append(row);});
}
async function refresh(){
  if(busy)return;busy=true;$('refresh').disabled=true;
  try{
    const [catalog,ledger,status]=await Promise.all([api('/products'),api('/orders'),api('/status')]);
    products=catalog;orders=ledger;
    if(!$('product').value){$('product').replaceChildren(...products.map(p=>{const option=node('option',`${p.name} · ${money(p.price_cents)}`);option.value=p.id;return option;}));}
    renderOrders();estimate();services(status);
    $('total').textContent=status.summary.orders;$('pending').textContent=status.summary.pending;$('revenue').textContent=money(status.summary.revenue_cents);
    $('sync-text').textContent=`Updated ${new Date().toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'})}`;
    $('error').hidden=true;$('submit').disabled=false;
  }catch(error){$('error').textContent=`Unable to refresh. ${error.message} Displayed orders may be out of date.`;$('error').hidden=false;$('sync-text').textContent='Connection interrupted';$('services').replaceChildren(node('li','Service status unavailable'));}
  finally{busy=false;$('refresh').disabled=false;}
}
$('order-form').addEventListener('submit',async event=>{
  event.preventDefault();$('submit').disabled=true;$('form-message').textContent='Creating order…';
  try{const order=await api('/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer_name:$('customer').value,product_id:Number($('product').value),quantity:Number($('quantity').value)})});$('form-message').textContent=`Order #OD-${String(order.id).padStart(4,'0')} created. Fulfillment is on its way.`;$('customer').value='';await refresh();}
  catch(error){$('form-message').textContent=error.name==='TimeoutError'?'The request timed out. Refresh the ledger before retrying to avoid a duplicate order.':error.message;}
  finally{$('submit').disabled=false;}
});
$('filter').addEventListener('change',renderOrders);$('product').addEventListener('change',estimate);$('quantity').addEventListener('input',estimate);$('refresh').addEventListener('click',refresh);
refresh();setInterval(refresh,5000);
