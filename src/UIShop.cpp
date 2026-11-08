#include "UIShop.h"
#include "Event.h"
#include "Font.h"
#include "PotConv.h"
#include "Save.h"
#include "TextureManager.h"
#include "strfunc.h"

// 按"显示宽度"补空格（CJK=2、ASCII=1），保证多行文本列对齐
static std::string pad_units(const std::string& s, int units)
{
    int w = Font::getTextDrawSize(s);
    if (w >= units)
    {
        return s;
    }
    return s + std::string(units - w, ' ');
}

UIShop::UIShop()
{
    plan_buy_.resize(SHOP_ITEM_COUNT, 0);
    for (int i = 0; i < SHOP_ITEM_COUNT; i++)
    {
        auto text = std::make_shared<Button>();
        text->setFontSize(24);
        text->setSize(SHOP_ROW_WIDTH, SHOP_ROW_HEIGHT);
        text->setHaveBox(false);
        text->setTextColor(SHOP_TEXT_COLOR, SHOP_TEXT_ACTIVE_COLOR, SHOP_TEXT_ACTIVE_COLOR);
        addChild(text, 0, 30 + SHOP_ROW_HEIGHT * i);

        // 原版用 title/104、105 两张箭头图，DOS 资源里没有，改成文字
        auto button_left = std::make_shared<Button>();
        text->addChild(button_left, 36 * 12 + 36, 2);
        button_left->setText("<");
        button_left->setFontSize(20);
        button_left->setHaveBox(false);
        button_left->setTextColor({ 220, 220, 220, 255 }, { 255, 220, 130, 255 }, { 255, 200, 90, 255 });
        buttons_.push_back(button_left);

        auto button_right = std::make_shared<Button>();
        text->addChild(button_right, 36 * 12 + 108, 2);
        button_right->setText(">");
        button_right->setFontSize(20);
        button_right->setHaveBox(false);
        button_right->setTextColor({ 220, 220, 220, 255 }, { 255, 220, 130, 255 }, { 255, 200, 90, 255 });
        buttons_.push_back(button_right);
    }
    button_ok_ = std::make_shared<Button>();
    button_ok_->setText("確認");
    addChild(button_ok_, SHOP_BUTTON_X, 30 + SHOP_ROW_HEIGHT * (SHOP_ITEM_COUNT + 1));
    button_cancel_ = std::make_shared<Button>();
    button_cancel_->setText("取消");
    addChild(button_cancel_, SHOP_BUTTON_X + SHOP_BUTTON_GAP, 30 + SHOP_ROW_HEIGHT * (SHOP_ITEM_COUNT + 1));
    button_clear_ = std::make_shared<Button>();
    button_clear_->setText("清除");
    addChild(button_clear_, SHOP_BUTTON_X + SHOP_BUTTON_GAP * 2, 30 + SHOP_ROW_HEIGHT * (SHOP_ITEM_COUNT + 1));

    //的前面几个是物品项，后面3个是按钮
}

UIShop::~UIShop()
{
}

void UIShop::setShopID(int id)
{
    shop_ = Save::getInstance()->getShop(id);
}

void UIShop::onEntrance()
{
    int ui_width = Engine::getInstance()->getUIWidth();
    int ui_height = Engine::getInstance()->getUIHeight();
    setPosition(ui_width / 2 - SHOP_BOX_WIDTH / 2, ui_height / 2 - SHOP_PANEL_HEIGHT / 2);
}

void UIShop::draw()
{
    Engine::getInstance()->fillColor({ 0, 0, 0, 128 }, 0, 0, -1, -1);
    int x = x_, y = y_;

    std::string str;
    auto font = Font::getInstance();

    if (textureReady("title", 126))
    {
        TextureManager::getInstance()->renderTexture("title", 126, x + SHOP_BOX_X, y + SHOP_BOX_Y, { { 255, 255, 255, 255 }, 255 }, SHOP_BOX_WIDTH, SHOP_BOX_HEIGHT);
    }
    else
    {
        // 没有菜单底板贴图，用深色实底代替，否则表格压在场景上看不清
        Engine::getInstance()->fillColor({ 0, 0, 0, 210 }, x + SHOP_BOX_X, y + SHOP_BOX_Y, SHOP_BOX_WIDTH, SHOP_BOX_HEIGHT);
    }

    // 注意：CJK 字符在 Font 里占 2 个单位，ASCII 占 1 个，所以必须按显示宽度补空格，
    // 不能用 std::format 的宽度（它按字符数算），否则表头和数据列对不上。
    str = pad_units("品名", 14) + pad_units("價格", 8) + pad_units("存貨", 8) + pad_units("持有", 8) + pad_units("計劃", 8);
    font->draw(str, 24, x, y, { 200, 150, 50, 255 });

    for (int i = 0; i < 5; i++)
    {
        auto item = Save::getInstance()->getItem(shop_->ItemID[i]);
        int count = Save::getInstance()->getItemCountInBag(item->ID);
        str = pad_units(item->Name, 14)
            + pad_units(std::to_string(shop_->Price[i]), 8)
            + pad_units(std::to_string(shop_->Total[i]), 8)
            + pad_units(std::to_string(count), 8)
            + pad_units(std::to_string(plan_buy_[i]), 8);
        //str = std::format("{:12}{:8}{:8}{:8}{:8}", item->Name, shop_->Price[i], shop_->Total[i], count, plan_buy_[i]);
        //std::string m = PotConv::utf8tocp936((char*)str1.c_str());
        //std::cout << m << "\n";
        ((Button*)(getChild(i).get()))->setText(str);
    }

    int need_money = calNeedMoney();
    str = std::format("總計銀兩{:8}", need_money);
    font->draw(str, 24, x + SHOP_MONEY_X, y + 30 + SHOP_ITEM_COUNT * SHOP_ROW_HEIGHT, SHOP_TEXT_COLOR);

    Color c = SHOP_TEXT_COLOR;
    int money = Save::getInstance()->getMoneyCountInBag();
    str = std::format("持有銀兩{:8}", money);
    if (money < need_money)
    {
        c = SHOP_MONEY_WARNING_COLOR;
    }
    font->draw(str, 24, x + SHOP_MONEY_X, y + 30 + (SHOP_ITEM_COUNT + 1) * SHOP_ROW_HEIGHT, c);
}

void UIShop::dealEvent(EngineEvent& e)
{
    static int first_press = 0;
    if (e.type == EVENT_KEY_DOWN && (e.key.key == K_LEFT || e.key.key == K_RIGHT) && active_child_ < SHOP_ITEM_COUNT)
    {
        if (first_press == 0 || first_press > 5)    //按一下的时候只走一格
        {
            int index = active_child_;
            if (e.key.key == K_LEFT)
            {
                if (plan_buy_[index] > 0)
                {
                    plan_buy_[index]--;
                }
            }
            else
            {
                if (plan_buy_[index] < shop_->Total[index])
                {
                    plan_buy_[index]++;
                }
            }
        }
        first_press++;
    }
    else
    {
        Menu::dealEvent(e);
    }
    if (e.type == EVENT_KEY_UP)
    {
        first_press = 0;
    }
    //LOG("%d ", first_press);
}

void UIShop::onPressedOK()
{
    for (int i = 0; i < SHOP_ITEM_COUNT * 2; i++)
    {
        if (buttons_[i]->getState() == NodePress)
        {
            int index = i / 2;
            int lr = i % 2;
            if (lr == 0)
            {
                if (plan_buy_[index] > 0)
                {
                    plan_buy_[index]--;
                }
            }
            else
            {
                if (plan_buy_[index] < shop_->Total[index])
                {
                    plan_buy_[index]++;
                }
            }
        }
    }
    if (button_ok_->getState() == NodePress)
    {
        if (calNeedMoney() <= Save::getInstance()->getMoneyCountInBag())
        {
            auto menu = std::make_shared<MenuText>();
            menu->setStrings({ "確認", "取消" });
            menu->setPosition(Engine::getInstance()->getUIWidth() / 2 - 75,
                Engine::getInstance()->getUIHeight() / 2 - 50);
            menu->setFontSize(24);
            menu->setHaveBox(true);
            menu->setText("確認購買？");
            menu->arrange(0, 50, 150, 0);
            if (menu->run() == 0)
            {
                for (int i = 0; i < SHOP_ITEM_COUNT; i++)
                {
                    Event::getInstance()->addItemWithoutHint(shop_->ItemID[i], plan_buy_[i]);
                    shop_->Total[i] -= plan_buy_[i];
                }
                Event::getInstance()->addItemWithoutHint(Item::MoneyItemID, -calNeedMoney());
                exitWithResult(0);
            }
        }
        else
        {
            auto text = std::make_shared<TextBox>();
            text->setText("銀兩不足");
            text->setFontSize(24);
            text->setTextColor(SHOP_MONEY_WARNING_COLOR);
            text->runAtPosition(Engine::getInstance()->getUIWidth() / 2 - 60,
                Engine::getInstance()->getUIHeight() / 2 - 12);
        }
    }
    if (button_cancel_->getState() == NodePress)
    {
        exitWithResult(-1);
    }
    if (button_clear_->getState() == NodePress)
    {
        for (int i = 0; i < SHOP_ITEM_COUNT; i++)
        {
            plan_buy_[i] = 0;
        }
    }
}

int UIShop::calNeedMoney()
{
    int need_money = 0;
    for (int i = 0; i < SHOP_ITEM_COUNT; i++)
    {
        need_money += plan_buy_[i] * shop_->Price[i];
    }
    return need_money;
}
