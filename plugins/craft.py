import assertpy
from itertools import chain

def inject(bot):
    Item = bot.registry['prismarine-item']
    Recipe = bot.registry['prismarine-recipe'].Recipe
    window_crafting_table = None

    async def craft(recipe, count, crafting_table):
        assertpy.assert_true(recipe)
        count = int(count) if count is not None else 1
        if recipe.requiresTable and not crafting_table:
            raise ValueError('recipe requires crafting_table')

        try:
            for _ in range(count):
                await craft_once(recipe, crafting_table)

            if window_crafting_table:
                bot.close_window(window_crafting_table)
                window_crafting_table = None
        except Exception as e:
            if window_crafting_table:
                bot.close_window(window_crafting_table)
                window_crafting_table = None
            raise ValueError(e)

    async def craft_once(recipe, crafting_table):
        if crafting_table:
            if not window_crafting_table:
                bot.activate_block(crafting_table)
                window_crafting_table, _ = await bot.wait_for('window_open')

            if not window_crafting_table.type.startswith('minecraft:crafting'):
                raise ValueError('crafting: non crafting_table used as crafting_table')

            await start_clicking(window_crafting_table, 3, 3)
        else:
            await start_clicking(bot.inventory, 2, 2)

    async def start_clicking(window, w, h):
        def slot(x, y):
            return 1 + x + w * y

        async def put_materials_away():
            start = window.inventory_start
            end = window.inventory_end
            await bot.put_selected_item_range(start, end, window, original_source_slot)
            await grab_result()

        async def grab_result():
            assertpy.assert_equal(window.selected_item, None)

            item = Item(recipe.result.id, recipe.result.count, recipe.result.metadata)
            window.update_slot(0, item)
            await bot.put_away(0)
            await update_out_shape()

        async def update_out_shape():
            if not recipe.outShape:
                for i in range(1, w * h + 1):
                    window.update_slot(i, None)
                return

            slots_to_click = []
            for y, row in enumerate(recipe.outShape):
                for x, slot_data in enumerate(row):
                    slot_id = slot(x, y)
                    item = None
                    if slot_data.id != -1:
                        item = Item(slot_data.id, slot_data.count, slot_data.metadata)
                        slots_to_click.append(slot_id)
                    window.update_slot(slot_id, item)

            for slot_id in slots_to_click:
                await bot.put_away(slot_id)

        async def next_shape_click():
            nonlocal it

            if increment_shape_iterator():
                await click_shape()
            elif not recipe.ingredients:
                await put_materials_away()
            else:
                await next_ingredients_click()

        async def click_shape():
            dest_slot = slot(it['x'], it['y'])
            ingredient = it['row'][it['x']]

            if ingredient.id == -1:
                return await next_shape_click()

            if not window.selected_item or window.selected_item.type != ingredient.id or (
                    ingredient.metadata is not None and window.selected_item.metadata != ingredient.metadata):
                source_item = window.find_inventory_item(ingredient.id, ingredient.metadata)
                if not source_item:
                    raise ValueError('missing ingredient')

                if original_source_slot is None:
                    original_source_slot = source_item.slot

                await bot.click_window(source_item.slot, 0, 0)

            await bot.click_window(dest_slot, 1, 0)
            await next_shape_click()

        async def next_ingredients_click():
            nonlocal ingredient_index

            ingredient = recipe.ingredients[ingredient_index]
            dest_slot = extra_slots.pop()

            if not window.selected_item or window.selected_item.type != ingredient.id or (
                    ingredient.metadata is not None and window.selected_item.metadata != ingredient.metadata):
                source_item = window.find_inventory_item(ingredient.id, ingredient.metadata)
                if not source_item:
                    raise ValueError('missing ingredient')

                if original_source_slot is None:
                    original_source_slot = source_item.slot

                await bot.click_window(source_item.slot, 0, 0)

            await bot.click_window(dest_slot, 1, 0)
            ingredient_index += 1

            if ingredient_index < len(recipe.ingredients):
                await next_ingredients_click()
            else:
                await put_materials_away()

        def increment_shape_iterator():
            it['x'] += 1

            if it['x'] >= len(it['row']):
                it['y'] += 1

                if it['y'] >= len(recipe.inShape):
                    return None

                it['x'] = 0
                it['row'] = recipe.inShape[it['y']]

            return it

        recipe = recipe.value if hasattr(recipe, 'value') else recipe
        count = count.value if hasattr(count, 'value') else count

        count = int(count)

        if not isinstance(recipe, Recipe):
            recipe = Recipe(recipe)

        if recipe.requiresTable and not crafting_table:
            raise ValueError('recipe requires crafting_table')

        if crafting_table:
            if not window_crafting_table:
                bot.activate_block(crafting_table)
                window_crafting_table, _ = await bot.wait_for('window_open')

            if not window_crafting_table.type.startswith('minecraft:crafting'):
                raise ValueError('crafting: non crafting_table used as crafting_table')

            await start_clicking(window_crafting_table, 3, 3)
        else:
            await start_clicking(bot.inventory, 2, 2)

        if window_crafting_table:
            bot.close_window(window_crafting_table)
            window_crafting_table = None

    async def start_clicking(window, w, h):
        def slot(x, y):
            return 1 + x + w * y

        async def put_materials_away():
            start = window.inventory_start
            end = window.inventory_end
            await bot.put_selected_item_range(start, end, window, original_source_slot)
            await grab_result()

        async def grab_result():
            assertpy.assert_equal(window.selected_item, None)

            item = Item(recipe.result.id, recipe.result.count, recipe.result.metadata)
            window.update_slot(0, item)
            await bot.put_away(0)
            await update_out_shape()

        async def update_out_shape():
            if not recipe.outShape:
                for i in range(1, w * h + 1):
                    window.update_slot(i, None)
                return

            slots_to_click = []
            for y, row in enumerate(recipe.outShape):
                for x, slot_data in enumerate(row):
                    slot_id = slot(x, y)
                    item = None
                    if slot_data.id != -1:
                        item = Item(slot_data.id, slot_data.count, slot_data.metadata)
                        slots_to_click.append(slot_id)
                    window.update_slot(slot_id, item)

            for slot_id in slots_to_click:
                await bot.put_away(slot_id)

        async def next_shape_click():
            nonlocal it

            if increment_shape_iterator():
                await click_shape()
            elif not recipe.ingredients:
                await put_materials_away()
            else:
                await next_ingredients_click()

        async def click_shape():
            dest_slot = slot(it['x'], it['y'])
            ingredient = it['row'][it['x']]

            if ingredient.id == -1:
                return await next_shape_click()

            if not window.selected_item or window.selected_item.type != ingredient.id or (
                    ingredient.metadata is not None and window.selected_item.metadata != ingredient.metadata):
                source_item = window.find_inventory_item(ingredient.id, ingredient.metadata)
                if not source_item:
                    raise ValueError('missing ingredient')

                if original_source_slot is None:
                    original_source_slot = source_item.slot

                await bot.click_window(source_item.slot, 0, 0)

            await bot.click_window(dest_slot, 1, 0)
            await next_shape_click()

        async def next_ingredients_click():
            nonlocal ingredient_index

            ingredient = recipe.ingredients[ingredient_index]
            dest_slot = extra_slots.pop()

            if not window.selected_item or window.selected_item.type != ingredient.id or (
                    ingredient.metadata is not None and window.selected_item.metadata != ingredient.metadata):
                source_item = window.find_inventory_item(ingredient.id, ingredient.metadata)
                if not source_item:
                    raise ValueError('missing ingredient')

                if original_source_slot is None:
                    original_source_slot = source_item.slot

                await bot.click_window(source_item.slot, 0, 0)

            await bot.click_window(dest_slot, 1, 0)
            ingredient_index += 1

            if ingredient_index < len(recipe.ingredients):
                await next_ingredients_click()
            else:
                await put_materials_away()

        def increment_shape_iterator():
            it['x'] += 1

            if it['x'] >= len(it['row']):
                it['y'] += 1

                if it['y'] >= len(recipe.inShape):
                    return None

                it['x'] = 0
                it['row'] = recipe.inShape[it['y']]

            return it

        recipe = recipe.value if hasattr(recipe, 'value') else recipe
        count = count.value if hasattr(count, 'value') else count

        count = int(count)

        if not isinstance(recipe, Recipe):
            recipe = Recipe(recipe)

        if recipe.requiresTable and not crafting_table:
            raise ValueError('recipe requires crafting_table')

        if crafting_table:
            if not window_crafting_table:
                bot.activate_block(crafting_table)
                window_crafting_table, _ = await bot.wait_for('window_open')

            if not window_crafting_table.type.startswith('minecraft:crafting'):
                raise ValueError('crafting: non crafting_table used as crafting_table')

            await start_clicking(window_crafting_table, 3, 3)
        else:
            await start_clicking(bot.inventory, 2, 2)

        if window_crafting_table:
            bot.close_window(window_crafting_table)
            window_crafting_table = None

    def recipes_for(item_type, metadata, min_result_count, crafting_table):
        min_result_count = min_result_count if min_result_count is not None else 1
        results = []

        for recipe in Recipe.find(item_type, metadata):
            if requirements_met_for_recipe(recipe, min_result_count, crafting_table):
                results.append(recipe)

        return results

    def recipes_all(item_type, metadata, crafting_table):
        results = []

        for recipe in Recipe.find(item_type, metadata):
            if not recipe.requiresTable or crafting_table:
                results.append(recipe)

        return results

    def requirements_met_for_recipe(recipe, min_result_count, crafting_table):
        if recipe.requiresTable and not crafting_table:
            return False

        craft_count = -(-min_result_count // recipe.result.count)  # Equivalent to math.ceil(min_result_count / recipe.result.count)

        for delta in recipe.delta:
            if bot.inventory.count(delta.id, delta.metadata) + delta.count * craft_count < 0:
                return False

        return True

    bot.craft = craft
    bot.recipes_for = recipes_for
    bot.recipes_all = recipes_all
