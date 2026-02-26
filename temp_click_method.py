    async def _click(self, context: BrowserContext, element_description: str) -> ToolResult:
        """
        简化的点击操作，自动选择最佳策略：
        1. 如果是日期类描述，直接使用视觉模型
        2. 尝试通过 JavaScript 查找包含指定文字的元素
        3. 如果失败，使用视觉模型

        Args:
            context: 浏览器上下文
            element_description: 要点击的元素描述（如"搜索按钮"、"1月30日"）

        Returns:
            ToolResult
        """
        try:
            page = await context.get_current_page()
            await page.bring_to_front()
            await page.wait_for_load_state()

            logger.info(f"[click] 尝试点击: '{element_description}'")

            # 检查是否是日期类描述 - 纯数字或包含"日"、"月"
            is_date_like = (
                element_description.isdigit() or
                re.search(r'^\d+[日号]?$', element_description) or
                re.search(r'\d+月\d+[日号]?', element_description) or
                "日历" in element_description or
                "calendar" in element_description.lower()
            )

            if is_date_like:
                logger.info(f"[click] 检测到日期类描述，尝试 Playwright locator")
                # 提取数字
                match = re.search(r'(\d+)', element_description)
                if match:
                    day_num = match.group(1)
                    try:
                        # 使用 Playwright 定位日历中的日期
                        locator = page.locator(f"text={day_num}").last
                        if await locator.count() > 0:
                            # 找到精确匹配，点击第一个可见的
                            for i in range(await locator.count()):
                                el = locator.nth(i)
                                if await el.is_visible():
                                    box = await el.bounding_box()
                                    if box and box['y'] < 600:  # 只点击上半部分页面的元素
                                        click_x = box['x'] + box['width'] / 2
                                        click_y = box['y'] + box['height'] / 2
                                        logger.info(f"[click] 精确匹配: '{element_description}' at ({click_x:.0f}, {click_y:.0f})")
                                        await page.mouse.click(click_x, click_y)
                                        await asyncio.sleep(0.5)
                                        return ToolResult(
                                            output=f"[click] Playwright 点击日期: {day_num}"
                                        )
                    except Exception as e:
                        logger.debug(f"[click] Playwright 日期定位失败: {e}")

                # 回退到视觉模型
                return await self._execute_vision_action(context, f"点击日历中的{element_description}", "click")

            # 策略1: 使用 Playwright locator 精确查找（优先文字精确匹配）
            try:
                # 尝试精确文字匹配
                locator = page.get_by_text(element_description, exact=True)
                if await locator.count() > 0:
                    # 找到精确匹配，点击第一个可见的
                    for i in range(await locator.count()):
                        el = locator.nth(i)
                        if await el.is_visible():
                            text_content = await el.text_content()
                            box = await el.bounding_box()
                            if box and box['y'] < 600:  # 只点击上半部分页面的元素
                                click_x = box['x'] + box['width'] / 2
                                click_y = box['y'] + box['height'] / 2
                                logger.info(f"[click] 精确匹配: '{element_description}' at ({click_x:.0f}, {click_y:.0f})")
                                await page.mouse.click(click_x, click_y)
                                await asyncio.sleep(0.5)
                                return ToolResult(
                                    output=f"[click] 成功点击: '{element_description}' at ({click_x:.0f}, {click_y:.0f})"
                                )

                # 尝试包含文字匹配（但要求元素文字长度不能太长）
                locator = page.get_by_text(element_description, exact=False)
                if await locator.count() > 0:
                    for i in range(min(await locator.count(), 10)):  # 最多检查10个
                        el = locator.nth(i)
                        if await el.is_visible():
                            text_content = await el.text_content()
                            # 只接受文字长度不超过描述3倍的元素
                            if text_content and len(text_content.strip()) <= len(element_description) * 3:
                                box = await el.bounding_box()
                                if box and box['y'] < 600:
                                    click_x = box['x'] + box['width'] / 2
                                    click_y = box['y'] + box['height'] / 2
                                    logger.info(f"[click] 包含匹配: '{text_content[:30]}' at ({click_x:.0f}, {click_y:.0f})")
                                    await page.mouse.click(click_x, click_y)
                                    await asyncio.sleep(0.5)
                                    return ToolResult(
                                        output=f"[click] 成功点击: '{text_content[:30]}' at ({click_x:.0f}, {click_y:.0f})"
                                    )
            except Exception as e:
                logger.debug(f"[click] Playwright locator 失败: {e}")

            # 策略2: 回退到视觉模型
            logger.info(f"[click] JavaScript 未找到匹配元素，使用视觉模型")
            return await self._execute_vision_action(context, f"点击{element_description}", "click")

        except Exception as e:
            logger.error(f"[click] 点击失败: {e}")
            # 最终回退到视觉模型
            return await self._execute_vision_action(context, f"点击{element_description}", "click")