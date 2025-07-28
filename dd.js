process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
import axios from 'axios';
import {HttpsProxyAgent} from 'https-proxy-agent';

const url = 'https://geo.brdtest.com/welcome.txt?product=dc&method=native';
const proxy = 'http://brd-customer-hl_3fa1037b-zone-datacenter_proxy1-country-ng:be0682squyj3@brd.superproxy.io:33335';

(async()=>{
  try {
    const response = await axios.get(url, {
      httpsAgent: new HttpsProxyAgent(proxy)
    });
    console.log(JSON.stringify(response.data, null, 2));
  } catch(error){
    console.error('Error:', error.message);
  }
})();
