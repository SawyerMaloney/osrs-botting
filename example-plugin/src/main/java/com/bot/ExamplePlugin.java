package com.bot;
import com.google.inject.Provides;
import javax.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import net.runelite.api.ChatMessageType;
import net.runelite.api.Client;
import net.runelite.api.GameState;
import net.runelite.api.Item;
import net.runelite.api.ItemContainer;
import net.runelite.api.InventoryID;
import net.runelite.api.events.GameStateChanged;
import net.runelite.client.config.ConfigManager;
import net.runelite.client.eventbus.Subscribe;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.callback.ClientThread;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.HashMap;
import java.util.Map;
import com.google.gson.Gson;
import java.util.Timer;
import java.util.TimerTask;

@Slf4j
@PluginDescriptor(
    name = "Example"
)
public class ExamplePlugin extends Plugin
{
    @Inject
    private Client client;
    
    @Inject
    private ClientThread clientThread;  // ADD THIS
    
    @Inject
    private ExampleConfig config;
    
    private WebSocketClient wsClient;
    private Timer wsTimer;
    private final Gson gson = new Gson();
    
    @Override
    protected void startUp() throws Exception
    {
        log.info("Example started!");
        
        try {
            wsClient = new WebSocketClient(new URI("ws://localhost:8765")) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    log.info("WebSocket connected");
                }
                
                @Override
                public void onMessage(String message) {
                    log.info("WebSocket received: {}", message);
                    if ("get_inv".equalsIgnoreCase(message.trim())) {
                        // Use clientThread to safely access the client API
                        clientThread.invoke(() -> {
                            String invJson = getInventoryJson();
                            wsClient.send(invJson);
                            log.info("Sent inventory JSON: {}", invJson);
                        });
                    }
                }
                
                @Override
                public void onClose(int code, String reason, boolean remote) {
                    log.info("WebSocket closed: {}", reason);
                }
                
                @Override
                public void onError(Exception ex) {
                    log.error("WebSocket error", ex);
                }
            };
            wsClient.connect();
        } catch (URISyntaxException e) {
            log.error("WebSocket URI error", e);
        }
        
        wsTimer = new Timer();
        wsTimer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                if (wsClient != null && !wsClient.isOpen()) {
                    try {
                        wsClient.reconnect();
                    } catch (Exception e) {
                        log.error("WebSocket reconnect error", e);
                    }
                }
            }
        }, 1000, 1000);
    }
    
    @Override
    protected void shutDown() throws Exception
    {
        log.info("Example stopped!");
        if (wsTimer != null) {
            wsTimer.cancel();
        }
        if (wsClient != null) {
            wsClient.close();
        }
    }
    
    @Subscribe
    public void onGameStateChanged(GameStateChanged gameStateChanged)
    {
        if (gameStateChanged.getGameState() == GameState.LOGGED_IN)
        {
            client.addChatMessage(ChatMessageType.GAMEMESSAGE, "", "Example says " + config.greeting(), null);
        }
    }
    
    /**
     * Get inventory as JSON: {"itemName": quantity, ...}
     * MUST be called from the client thread!
     */
    private String getInventoryJson() {
        Map<String, Integer> inv = new HashMap<>();
        if (client == null) return gson.toJson(inv);
        
        ItemContainer invContainer = client.getItemContainer(InventoryID.INVENTORY);
        if (invContainer == null) return gson.toJson(inv);
        
        Item[] items = invContainer.getItems();
        for (Item item : items) {
            if (item == null || item.getId() <= 0 || item.getQuantity() <= 0) continue;
            String name = client.getItemDefinition(item.getId()).getName();
            inv.put(name, inv.getOrDefault(name, 0) + item.getQuantity());
        }
        
        return gson.toJson(inv);
    }
    
    @Provides
    ExampleConfig provideConfig(ConfigManager configManager)
    {
        return configManager.getConfig(ExampleConfig.class);
    }
}