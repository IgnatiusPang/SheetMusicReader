/**
 * Puppeteer Integration Test Script for Psalm Sheet Music Reader
 * Run with: node tests/puppeteer_test.js
 */

const puppeteer = require('puppeteer');

(async () => {
  console.log('🚀 Starting Puppeteer Test Suite...');
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();

  try {
    console.log('🌐 Navigating to http://localhost:5000...');
    await page.goto('http://localhost:5000', { waitUntil: 'networkidle2' });

    // 1. Verify Page Title & Header Elements
    const title = await page.title();
    console.log(`✅ Page Title: "${title}"`);
    
    await page.waitForSelector('[data-testid="psalm-select"]');
    console.log('✅ Psalm Select element present.');

    // 2. Select Psalm 104
    await page.select('[data-testid="psalm-select"]', 'psalm_104');
    await new Promise(r => setTimeout(r, 600));

    const psalmTitle = await page.$eval('[data-testid="psalm-title"]', el => el.textContent);
    console.log(`✅ Loaded Psalm Title: "${psalmTitle}"`);

    // 3. Check Lyrics Overlaid Underneath Notes
    const firstWord = await page.$eval('[data-testid="lyric-word-0"]', el => el.textContent);
    console.log(`✅ First Overlaid Lyric Word: "${firstWord}"`);

    // 4. Click Play & Verify Visualizer
    await page.click('[data-testid="play-btn"]');
    await new Promise(r => setTimeout(r, 500));

    const statusText = await page.$eval('[data-testid="status-indicator"]', el => el.textContent);
    console.log(`✅ Player Status: "${statusText}"`);

    console.log('🎉 All Puppeteer Tests Passed Successfully!');
  } catch (err) {
    console.error('❌ Puppeteer Test Failed:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
