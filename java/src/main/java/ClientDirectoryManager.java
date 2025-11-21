import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import ghidra.program.model.listing.Program;
import ghidra.util.Msg;

/**
 * ClientDirectoryManager maintains information about connected clients 
 * and provides directory services similar to Ghidra's CodeBrowser functionality
 */
public class ClientDirectoryManager {
	
	// Map to store connected clients
	private Map<String, ClientInfo> connectedClients;
	
	// Map to store comment information
	private Map<String, List<CommentInfo>> commentsByAddress;
	
	// Reference to the main plugin for accessing program state
	private GhidraTCPCommentingPlugin plugin;

	/**
	 * Constructor for ClientDirectoryManager
	 * @param plugin Reference to the main plugin
	 */
	public ClientDirectoryManager(GhidraTCPCommentingPlugin plugin) {
		this.plugin = plugin;
		this.connectedClients = new ConcurrentHashMap<>();
		this.commentsByAddress = new ConcurrentHashMap<>();
	}
	
	/**
	 * Register a new client with the directory
	 * @param clientId Unique identifier for the client
	 * @param clientInfo Information about the client
	 */
	public void registerClient(String clientId, ClientInfo clientInfo) {
		connectedClients.put(clientId, clientInfo);
		Msg.info(this, "Client registered: " + clientId + " at " + clientInfo.getAddress());
	}
	
	/**
	 * Unregister a client from the directory
	 * @param clientId Unique identifier for the client
	 */
	public void unregisterClient(String clientId) {
		ClientInfo clientInfo = connectedClients.remove(clientId);
		if (clientInfo != null) {
			Msg.info(this, "Client unregistered: " + clientId + " at " + clientInfo.getAddress());
		}
	}
	
	/**
	 * Get information about all connected clients
	 * @return List of client information
	 */
	public List<ClientInfo> getConnectedClients() {
		return new ArrayList<>(connectedClients.values());
	}
	
	/**
	 * Add a comment at a specific address in the current program
	 * @param address The address where the comment is added
	 * @param commentText The text of the comment
	 * @param clientId The ID of the client adding the comment
	 * @return true if successful, false otherwise
	 */
	public boolean addComment(String address, String commentText, String clientId) {
		Program currentProgram = plugin.getCurrentProgram();
		if (currentProgram == null) {
			Msg.error(this, "No program loaded, cannot add comment");
			return false;
		}
		
		CommentInfo comment = new CommentInfo(address, commentText, clientId, new Date());
		
		commentsByAddress.computeIfAbsent(address, k -> new ArrayList<>()).add(comment);
		Msg.info(this, "Comment added at " + address + " by client " + clientId + ": " + commentText);
		
		return true;
	}
	
	/**
	 * Get comments for a specific address
	 * @param address The address to get comments for
	 * @return List of comments for the address
	 */
	public List<CommentInfo> getCommentsForAddress(String address) {
		List<CommentInfo> comments = commentsByAddress.get(address);
		return comments != null ? new ArrayList<>(comments) : new ArrayList<>();
	}
	
	/**
	 * Get all comments in the current program
	 * @return Map of address to list of comments
	 */
	public Map<String, List<CommentInfo>> getAllComments() {
		Map<String, List<CommentInfo>> result = new HashMap<>();
		for (Map.Entry<String, List<CommentInfo>> entry : commentsByAddress.entrySet()) {
			result.put(entry.getKey(), new ArrayList<>(entry.getValue()));
		}
		return result;
	}
	
	/**
	 * Get information about the current program
	 * @return Program information
	 */
	public ProgramInfo getCurrentProgramInfo() {
		Program currentProgram = plugin.getCurrentProgram();
		if (currentProgram == null) {
			return null;
		}
		
		return new ProgramInfo(
			currentProgram.getName(),
			currentProgram.getExecutablePath(),
			currentProgram.getLanguage().getProcessor().toString(),
			currentProgram.getLanguage().getLanguageDescription().getSize(),
			String.valueOf(currentProgram.getMinAddress()),
			String.valueOf(currentProgram.getMaxAddress())
		);
	}
	
	/**
	 * Inner class to represent information about a connected client
	 */
	public static class ClientInfo {
		private String id;
		private String address;
		private Date connectedSince;
		private String clientType;
		
		public ClientInfo(String id, String address, String clientType) {
			this.id = id;
			this.address = address;
			this.connectedSince = new Date();
			this.clientType = clientType;
		}
		
		public String getId() { return id; }
		public String getAddress() { return address; }
		public Date getConnectedSince() { return connectedSince; }
		public String getClientType() { return clientType; }
	}
	
	/**
	 * Inner class to represent a comment
	 */
	public static class CommentInfo {
		private String address;
		private String commentText;
		private String clientId;
		private Date timestamp;
		
		public CommentInfo(String address, String commentText, String clientId, Date timestamp) {
			this.address = address;
			this.commentText = commentText;
			this.clientId = clientId;
			this.timestamp = timestamp;
		}
		
		public String getAddress() { return address; }
		public String getCommentText() { return commentText; }
		public String getClientId() { return clientId; }
		public Date getTimestamp() { return timestamp; }
	}
	
	/**
	 * Inner class to represent program information
	 */
	public static class ProgramInfo {
		private String name;
		private String executablePath;
		private String processor;
		private int size;
		private String minAddress;
		private String maxAddress;
		
		public ProgramInfo(String name, String executablePath, String processor, int size, String minAddress, String maxAddress) {
			this.name = name;
			this.executablePath = executablePath;
			this.processor = processor;
			this.size = size;
			this.minAddress = minAddress;
			this.maxAddress = maxAddress;
		}
		
		public String getName() { return name; }
		public String getExecutablePath() { return executablePath; }
		public String getProcessor() { return processor; }
		public int getSize() { return size; }
		public String getMinAddress() { return minAddress; }
		public String getMaxAddress() { return maxAddress; }
	}
}