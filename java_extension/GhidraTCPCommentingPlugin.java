import java.awt.event.MouseEvent;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import docking.ActionContext;
import docking.action.DockingAction;
import docking.action.MenuData;
import docking.action.ToolBarData;
import ghidra.app.plugin.PluginCategoryNames;
import ghidra.app.plugin.ProgramPlugin;
import ghidra.framework.plugintool.*;
import ghidra.framework.plugintool.util.PluginStatus;
import ghidra.util.Msg;

/**
 * GhidraTCPCommentingPlugin is a plugin that provides TCP server functionality
 * for client communication and remote commenting capabilities.
 */
//@formatter:off
@PluginInfo(
	status = PluginStatus.STABLE,
	packageName = "GhidraTCPCommentingPlugin",
	category = PluginCategoryNames.COMMON,
	shortDescription = "TCP Commenting for client communication",
	description = "This plugin provides a TCP server for clients to communicate with Ghidra and add remote comments.",
	servicesRequired = {}
)
//@formatter:on
public class GhidraTCPCommentingPlugin extends ProgramPlugin {

	private int serverPort = 9000; // Default port for the TCP server
	private ServerSocket serverSocket;
	private ExecutorService executorService;
	private boolean serverRunning = false;
	private ClientDirectoryManager directoryManager;
	private String pluginName;

	/**
	 * Constructor for GhidraTCPCommentingPlugin
	 * @param tool The plugin tool that this plugin is added to
	 */
	public GhidraTCPCommentingPlugin(PluginTool tool) {
		super(tool, true, true);
		this.executorService = Executors.newCachedThreadPool();
		this.pluginName = getName();
		initialize();
		createActions();
	}

	/**
	 * Initializes the plugin
	 */
	private void initialize() {
		// Initialize the client directory manager
		this.directoryManager = new ClientDirectoryManager(this);
		Msg.info(this, "GhidraTCPCommentingPlugin initialized.");
	}

	/**
	 * Creates the actions available in the plugin
	 */
	private void createActions() {
		// Create action to start the TCP server
		DockingAction startServerAction = new DockingAction("Start TCP Server", getName()) {
			@Override
			public void actionPerformed(ActionContext context) {
				startTCPServer();
			}
		};
		startServerAction.setMenuBarData(new MenuData(new String[] { "Tools", "Start TCP Server" }));
		startServerAction.setEnabled(true);
		tool.addAction(startServerAction);

		// Create action to stop the TCP server
		DockingAction stopServerAction = new DockingAction("Stop TCP Server", getName()) {
			@Override
			public void actionPerformed(ActionContext context) {
				stopTCPServer();
			}
		};
		stopServerAction.setMenuBarData(new MenuData(new String[] { "Tools", "Stop TCP Server" }));
		stopServerAction.setEnabled(serverRunning);
		tool.addAction(stopServerAction);
	}

	/**
	 * Starts the TCP server
	 */
	private void startTCPServer() {
		if (serverRunning) {
			Msg.info(this, "TCP server is already running on port " + serverPort);
			return;
		}

		try {
			serverSocket = new ServerSocket(serverPort);
			serverRunning = true;
			Msg.info(this, "TCP server started on port " + serverPort);

			// Start accepting client connections in a separate thread
			executorService.submit(() -> {
				while (serverRunning) {
					try {
						Socket clientSocket = serverSocket.accept();
						// Handle each client in a separate thread
						executorService.submit(new ClientConnectionHandler(clientSocket));
					} catch (IOException e) {
						if (serverRunning) { // Only log if not intentionally closed
							Msg.error(this, "Error accepting client connection", e);
						}
					}
				}
			});
		} catch (IOException e) {
			Msg.error(this, "Error starting TCP server on port " + serverPort, e);
		}
	}

	/**
	 * Stops the TCP server
	 */
	private void stopTCPServer() {
		if (!serverRunning) {
			Msg.info(this, "TCP server is not running");
			return;
		}

		try {
			serverRunning = false;
			if (serverSocket != null && !serverSocket.isClosed()) {
				serverSocket.close();
			}
			Msg.info(this, "TCP server stopped");
		} catch (IOException e) {
			Msg.error(this, "Error stopping TCP server", e);
		}
	}

	/**
	 * Inner class to initiate client connections
	 */
	private class ClientConnectionHandler implements Runnable {
		private Socket clientSocket;

		public ClientConnectionHandler(Socket socket) {
			this.clientSocket = socket;
		}

		@Override
		public void run() {
			// Handle client communication using the standalone ClientHandler class
			Msg.info(this, "Handling client connection using new handler: " + clientSocket.getRemoteSocketAddress());

			// Process client commands using the standalone ClientHandler class
			try {
				ClientHandler externalHandler = new ClientHandler(clientSocket, GhidraTCPCommentingPlugin.this);
				externalHandler.run();
			} catch (Exception e) {
				Msg.error(this, "Error in client handler", e);
			}
		}

		// Provide access to the directory manager
		public ClientDirectoryManager getDirectoryManager() {
			return directoryManager;
		}
	}

	@Override
	protected void dispose() {
		stopTCPServer();
		if (executorService != null) {
			executorService.shutdown();
		}
		super.dispose();
	}

	/**
	 * Get the client directory manager
	 * @return The ClientDirectoryManager instance
	 */
	public ClientDirectoryManager getDirectoryManager() {
		return directoryManager;
	}
}