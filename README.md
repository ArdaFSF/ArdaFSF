local Players = game:GetService("Players")
local Camera = game.Workspace.CurrentCamera

-- ESP'yi çizme fonksiyonu
local function drawESP(player)
    local function createESP(character)
        local head = character:WaitForChild("Head")

        -- BillboardGui oluşturuluyor (karakterin başı üzerinde ESP göstermek için)
        local billboardGui = Instance.new("BillboardGui")
        billboardGui.Name = "ESP"
        billboardGui.Adornee = head  -- Hedef: karakterin başı
        billboardGui.Size = UDim2.new(0, 200, 0, 50)  -- Boyut ayarı (görünür etiket boyutu)
        billboardGui.StudsOffset = Vector3.new(0, 2, 0)  -- Yükseklik offseti, etiketin biraz yukarıda görünmesi için
        billboardGui.AlwaysOnTop = true  -- Ekranın üstünde kalmasını sağla
        billboardGui.Parent = character

        -- TextLabel oluşturuluyor (oyuncu ismini yazmak için)
        local textLabel = Instance.new("TextLabel")
        textLabel.Size = UDim2.new(1, 0, 1, 0)
        textLabel.BackgroundTransparency = 1  -- Şeffaf arka plan
        textLabel.TextColor3 = Color3.fromRGB(255, 255, 255)  -- Beyaz metin rengi
        textLabel.TextSize = 16  -- Metin boyutu
        textLabel.Font = Enum.Font.SourceSansBold  -- Font türü
        textLabel.Text = player.Name  -- Oyuncunun adı
        textLabel.Parent = billboardGui

        -- Frame (Kare) çizme (oyuncunun etrafını saran kutu)
        local frame = Instance.new("Frame")
        frame.Size = UDim2.new(1, 0, 1, 0)  -- Tam boyutlu kare
        frame.BackgroundTransparency = 1  -- Şeffaf arka plan
        frame.BorderSizePixel = 2  -- Çerçeve kenarlığı
        frame.BorderColor3 = Color3.fromRGB(0, 255, 0)  -- Yeşil renk (kare için)
        frame.Parent = billboardGui

        -- Ekranda olup olmadığını kontrol etmek ve sadece ekranda görünmesini sağlamak
        game:GetService("RunService").Heartbeat:Connect(function()
            local onScreen, screenPos = Camera:WorldToViewportPoint(head.Position)
            if onScreen then
                billboardGui.Enabled = true  -- Eğer ekranın içinde, ESP'yi göster
                billboardGui.Position = UDim2.new(0, screenPos.X - frame.Size.X.Offset / 2, 0, screenPos.Y - frame.Size.Y.Offset / 2)
            else
                billboardGui.Enabled = false  -- Ekran dışındaysa, ESP'yi gizle
            end
        end)
    end

    -- Eğer oyuncunun karakteri varsa, ESP'yi çiz
    if player.Character then
        createESP(player.Character)
    end

    -- Oyuncu yeniden doğarsa, ESP'yi tekrar çiz
    player.CharacterAdded:Connect(function(character)
        createESP(character)
    end)
end

-- Yeni oyuncu geldiğinde ESP'yi etkinleştir
Players.PlayerAdded:Connect(function(player)
    player.CharacterAdded:Connect(function()
        drawESP(player)
    end)
end)

-- Mevcut oyunculara ESP çizme (oyuncu zaten oyun içindeyse)
for _, player in pairs(Players:GetPlayers()) do
    if player.Character then
        drawESP(player)
    end
end
