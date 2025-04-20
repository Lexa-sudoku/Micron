import asyncio
import json
from parsers.compile import parsing

async def run_test():
    product = input('Введите имя продукта: (AD620ANZ) ')
    result = await parsing(product)
    filename = f'test_pn-{product}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False))
    print(f'Результат сохранен в {filename}')

if __name__ == "__main__":
    asyncio.run(run_test())