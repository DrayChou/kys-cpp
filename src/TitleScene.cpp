#include "TitleScene.h"
#include "Audio.h"
#include "BattleScene.h"
#include "Button.h"
#include "Font.h"
#include "GameUtil.h"
#include "INIReader.h"
#include "InputBox.h"
#include "MainScene.h"
#include "Menu.h"
#include "Random.h"
#include "RandomRole.h"
#include "SubScene.h"
#include "UISave.h"
#include "Video.h"
#include "Weather.h"
#include <cstdlib>

int TitleScene::getTitleTextureID(int battle_mode)
{
    if (battle_mode == 2)
    {
        return 153;
    }
    return 154;
}

int TitleScene::getTitleTextureY(int texture_id)
{
    auto texture = TextureManager::getInstance()->getTexture("title", texture_id);
    if (texture == nullptr)
    {
        return 0;
    }
    texture->load();
    return (Engine::getInstance()->getUIHeight() - texture->h) / 2;
}

TitleScene::TitleScene()
{
    full_window_ = 1;
    battle_mode_ = GameUtil::getInstance()->getInt("game", "battle_mode");
    menu_ = std::make_shared<Menu>();
    menu_->setPosition(560, 550);
    // DOS 版素材里没有「新遊戲／讀取進度／離開遊戲」这三张按钮图（原图是舊版的進度選單），
    // 直接用文字画，避免图文错位。
    {
        auto b0 = menu_->addChild<Button>(-180, 0);
        b0->setText("新 游 戏");
        b0->setTextColor({255, 255, 255, 255}, {255, 220, 130, 255}, {255, 200, 90, 255});
    }
    {
        auto b1 = menu_->addChild<Button>(20, 0);
        b1->setText("读 取 进 度");
        b1->setTextColor({255, 255, 255, 255}, {255, 220, 130, 255}, {255, 200, 90, 255});
    }
    {
        auto b2 = menu_->addChild<Button>(220, 0);
        b2->setText("离 开 游 戏");
        b2->setTextColor({255, 255, 255, 255}, {255, 220, 130, 255}, {255, 200, 90, 255});
    }
    menu_load_ = std::make_shared<UISave>();
    menu_load_->setPosition(500, 300);
    //render_message_ = 1;

    if (battle_mode_ == 2)
    {
        auto pe1 = std::make_shared<ParticleExample>();
        pe1->setStyle(ParticleExample::FIRE);
        addChild(pe1);
        pe1->setPosition(490, 80);
        pe1->setSize(20, 20);
    }
    else if (battle_mode_ == 3)
    {
        auto pe1 = std::make_shared<ParticleExample>();
        pe1->setPosition(Engine::getInstance()->getWindowWidth() * 0.15, 0);
        pe1->setStyle(ParticleExample::RAIN);    //先设置位置，再设置样式，有var的问题
        pe1->setTotalParticles(2000);
        pe1->setPosVar({ float(Engine::getInstance()->getWindowWidth() * 0.85), -50 });
        pe1->resetSystem();
        pe1->setEmissionRate(200);
        pe1->setGravity({ 200, 50 });
        addChild(pe1);
    }
    //调试用代码
    //Save::getInstance()->load(5);
    RandomDouble rand;
    int k = rand.rand() * 139;
    k = 1;
    //Event::getInstance()->tryBattle(k, 0);

    //auto  p=std::make_shared<RunNodeFromJson>("../game/Scene.json");
    //addChild(p);
}

TitleScene::~TitleScene()
{
}

void TitleScene::draw()
{
    Engine::getInstance()->fillColor({ 0, 0, 0, 255 }, 0, 0, Engine::getInstance()->getWindowWidth(), Engine::getInstance()->getWindowHeight());
    int title_texture_id = getTitleTextureID(battle_mode_);
    TextureManager::getInstance()->renderTexture("title", title_texture_id, 0, getTitleTextureY(title_texture_id));
    Font::getInstance()->draw(GameUtil::VERSION(), 28, 0, 0);
    return;
    //屏蔽随机头像
    int count = count_ / 20;
    int alpha = 255 - abs(255 - count_ % 510);
    count_++;
    if (alpha == 0)
    {
        RandomDouble r;
        head_id_ = r.rand_int(115);
        head_x_ = r.rand_int(1280 - 150);
        head_y_ = r.rand_int(800 - 150);
    }
    TextureManager::getInstance()->renderTexture("head", head_id_, head_x_, head_y_, { { 255, 255, 255, 255 }, uint8_t(alpha) });
    //TextureManager::getInstance()->renderTexture("title", 150, 240, 150, { 255,255,255,255 }, 255, 0.3, 0.3);
}

void TitleScene::dealEvent(EngineEvent& e)
{
    int r = menu_->run();
    if (r == 0)
    {
        Engine::getInstance()->gameControllerRumble(50, 50, 500);
        // 没有默认存档时（用户删了 save/0.db），load 会返回 false，后面 getRole(0) 就是空指针。
        // 这里提前挡掉，避免直接崩在 0xC0000005。
        if (!Save::getInstance()->load(0) || Save::getInstance()->getRole(0) == nullptr)
        {
            LOG("没有可用的初始存档（save/0.db + allsin.grp + alldef.grp），无法开始新游戏");
            return;
        }
        std::string name = "";
        auto input = std::make_shared<InputBox>("請輸入姓名：", 30);
        input->setInputPosition(350, 300);
        input->setActionButtons(true);
        input->setText(Save::getInstance()->getRole(0)->Name);
        input->run();
        if (input->getResult() >= 0)
        {
            name = input->getText();
        }
        if (!name.empty())
        {
            auto random_role = std::make_shared<RandomRole>();
            random_role->setRole(Save::getInstance()->getRole(0));
            random_role->setRoleName(name);
            if (random_role->runAtPosition(300, 0) == 0)
            {
                MainScene::getInstance()->setManPosition(Save::getInstance()->MainMapX, Save::getInstance()->MainMapY);
                MainScene::getInstance()->setTowards(1);
                int s = GameUtil::getInstance()->getInt("constant", "begin_scene", 70);
                int x = GameUtil::getInstance()->getInt("constant", "begin_sx", 19);
                int y = GameUtil::getInstance()->getInt("constant", "begin_sy", 20);
                MainScene::getInstance()->forceEnterSubScene(s, x, y, GameUtil::getInstance()->getInt("constant", "begin_event", -1));
                MainScene::getInstance()->run();
            }
        }
    }
    if (r == 1)
    {
        if (menu_load_->run() >= 0)
        {
            //Save::getInstance()->getRole(0)->MagicLevel[0] = 900;    //测试用
            MainScene::getInstance()->run();
        }
    }
    if (r == 2)
    {
        setExit(true);
        exit(0);    //强制退出，否则在Android下可能退不完全
    }
}

void TitleScene::onEntrance()
{
    Video v(Engine::getInstance()->getWindow());
    v.playVideo(GameUtil::PATH() + "movie/1.mp4");
    Audio::getInstance()->playMusic(16);
}
