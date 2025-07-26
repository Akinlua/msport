const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const proxyChain = require('proxy-chain');

async function loadSiteWithProxy() {
    let driver;
    let newProxyUrl;
    
    try {
        // Proxy configuration
        const proxy = {
            username: 'brd-customer-hl_a9f8ae62-zone-residential_proxy2',
            password: '8eaw0hjl16bx', 
            host: 'brd.superproxy.io',
            port: '33335'
        };

        // Create the old proxy URL
        const oldProxyUrl = `http://${proxy.username}:${proxy.password}@${proxy.host}:${proxy.port}`;
        console.log('Original proxy URL:', oldProxyUrl.replace(/:([^:@]*@)/, ':***@'));

        // Anonymize the proxy
        newProxyUrl = await proxyChain.anonymizeProxy(oldProxyUrl);
        console.log('Anonymized proxy URL:', newProxyUrl);

        // Chrome options
        const options = new chrome.Options();
        options.addArguments('--headless=new');
        options.addArguments(`--proxy-server=http://ng.decodo.com:42001`);
        options.addArguments('--no-sandbox');
        options.addArguments('--disable-dev-shm-usage');
        options.addArguments('--disable-web-security');
        options.addArguments('--ignore-certificate-errors');
        options.addArguments('--ignore-ssl-errors');
        options.addArguments('--allow-running-insecure-content');
        
        // Optional: Run in headless mode
        // options.addArguments('--headless');

        // Create WebDriver instance
        driver = await new Builder()
            .forBrowser('chrome')
            .setChromeOptions(options)
            .build();

        console.log('WebDriver created successfully');

        // Navigate to IP checking sites
        const ipSites = [
            'https://www.msport.com/'
        ];

        for (const site of ipSites) {
            try {
                console.log(`\nLoading: ${site}`);
                await driver.get(site);
                
                // Wait for page to load
                await driver.wait(until.elementLocated(By.tagName('body')), 10000);
                
                // Get page content
                const pageContent = await driver.findElement(By.tagName('body')).getText();
                console.log('Response:', pageContent);
                
                // Wait a bit between requests
                await new Promise(resolve => setTimeout(resolve, 2000));
                
            } catch (error) {
                console.error(`Error loading ${site}:`, error.message);
            }
        }

        // Optional: Load a regular website to test
        console.log('\nLoading example.com...');
        await driver.get('https://example.com');
        const title = await driver.getTitle();
        await new Promise(resolve => setTimeout(resolve, 100000));
        console.log('Page title:', title);

    } catch (error) {
        console.error('Error:', error);
    } finally {
        // Cleanup
        if (driver) {
            await driver.quit();
            console.log('WebDriver closed');
        }
        
        if (newProxyUrl) {
            await proxyChain.closeAnonymizedProxy(newProxyUrl, true);
            console.log('Proxy chain closed');
        }
    }
}

// Handle process termination
process.on('SIGINT', async () => {
    console.log('\nReceived SIGINT, cleaning up...');
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\nReceived SIGTERM, cleaning up...');
    process.exit(0);
});

// Run the function
loadSiteWithProxy().catch(console.error);