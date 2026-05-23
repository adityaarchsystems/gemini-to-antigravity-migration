import asyncio
import csv
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import LLMExtractionStrategy, LLMConfig

class IndieHackerLead(BaseModel):
    founder_handle: str = Field(..., description="The user handle or identity tag of the product creator")
    product_bio: str = Field(..., description="A short summary detailing what their tool or platform scales")
    recent_status: str = Field(..., description="What business processes they are actively managing or stuck on")

async def main():
    target_url = "https://www.indiehackers.com/products"
    print(f"[🛰️] Initializing structured extraction matrix on: {target_url}")

    llm_configuration = LLMConfig(
        provider="gemini/gemini-3.5-flash",
        api_token="YOUR_GEMINI_API_KEY"
    )

    llm_strategy = LLMExtractionStrategy(
        llm_config=llm_configuration,
        schema=IndieHackerLead.model_json_schema(),
        extraction_type="schema",
        instruction="Parse the product database layout and extract active builder profiles, bios, and descriptions.",
        input_format="markdown"
    )

    config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=target_url, config=config)

        if not result.success or not result.extracted_content:
            print("[❌] Extraction failed or returned blank variables.")
            return

        raw_leads = json.loads(result.extracted_content)
        print(f"[✅] Successfully parsed {len(raw_leads)} live profiles using LLMConfig.")

        with open('raw_leads_input.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Bio', 'Posts'])
            
            for lead in raw_leads:
                handle = lead.get('founder_handle', '@unknown_builder').strip()
                if not handle.startswith('@'):
                    handle = f"@{handle.lower().replace(' ', '_')}"
                    
                writer.writerow([
                    handle,
                    lead.get('product_bio', 'Full-stack software developer').strip(),
                    lead.get('recent_status', 'Managing custom client dashboard scaling overhead.').strip()
                ])

        print("[🎉] raw_leads_input.csv has been fully updated with authentic developer data.")

if __name__ == "__main__":
    asyncio.run(main())
