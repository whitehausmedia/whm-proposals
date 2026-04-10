/**
 * Shopify OAuth Callback Handler
 * App URL: https://whm-proposals.vercel.app/api/shopify-token
 */
const CLIENT_ID     = '269d0fb89a36c702fe8733a0cb5dd78f';
const CLIENT_SECRET = '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';

export default async function handler(req, res) {
  const { code, shop } = req.query;
  if (!code || !shop) {
    return res.setHeader('Content-Type','text/html').send('<h1>Waiting for OAuth...</h1><p>Install app from Dev Dashboard to trigger callback.</p><p>Shop: '+(shop||'pending')+'</p>');
  }
  try {
    const tr = await fetch('https://'+shop+'/admin/oauth/access_token', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({client_id:CLIENT_ID, client_secret:CLIENT_SECRET, code})
    });
    if (!tr.ok) throw new Error('Token exchange failed: '+(await tr.text()));
    const { access_token: adminToken } = await tr.json();
    if (!adminToken) throw new Error('No access_token');
    const sr = await fetch('https://'+shop+'/admin/api/2024-01/graphql.json', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-Shopify-Access-Token':adminToken},
      body: JSON.stringify({query:'mutation{storefrontAccessTokenCreate(input:{title:"TrapxCanvas Headless v6"}){storefrontAccessToken{accessToken}userErrors{field message}}}'})
    });
    const sd = await sr.json();
    const sfToken = sd?.data?.storefrontAccessTokenCreate?.storefrontAccessToken?.accessToken;
    if (!sfToken) throw new Error('No SF token: '+JSON.stringify(sd));
    res.setHeader('Content-Type','text/html').send('<html><head><style>body{font-family:sans-serif;background:#0a0a0a;color:#f0f0f0;max-width:700px;margin:60px auto;padding:20px}h1{color:#00ff88}.box{background:#111;border:2px solid #00ff88;border-radius:8px;padding:24px;font-family:monospace;font-size:18px;color:#00ff88;word-break:break-all;margin:20px 0}button{background:#00ff88;color:#000;border:none;padding:10px 24px;border-radius:4px;cursor:pointer;font-size:16px;font-weight:bold}pre{background:#111;padding:16px;border-radius:4px;color:#aaa;word-break:break-all}</style></head><body><h1>Storefront Token!</h1><div class="box" id="t">'+sfToken+'</div><button onclick="navigator.clipboard.writeText(document.getElementById(\'t\').textContent).then(()=>this.textContent=\'Copied!\')">Copy</button><pre>const SHOPIFY_TOKEN = \''+sfToken+'\';</pre></body></html>');
  } catch(err) {
    res.status(500).setHeader('Content-Type','text/html').send('<h1>Error</h1><pre>'+err.message+'</pre><p>Shop: '+shop+' | Code: '+(code?'yes':'no')+'</p>');
  }
}
