import { useState, useEffect, useRef, useCallback } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, Conversation, ChatMessage, User } from "@/lib/api";
import { chatWebSocket, WebSocketMessage } from "@/lib/websocket";
import { useAuth } from "@/contexts/AuthContext";
import { formatDistanceToNow, format } from "date-fns";
import { Send, Search, Plus, MessageCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function Chat() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messageInput, setMessageInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<Set<number>>(new Set());
  const [newChatDialogOpen, setNewChatDialogOpen] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }, []);

  const handleWebSocketMessage = useCallback((data: WebSocketMessage) => {
    if (data.message) {
      // If message is for currently selected conversation, add it to local state
      if (data.conversation_id === selectedConversation?.id) {
        setMessages((prev) => {
          // Check if message already exists to prevent duplicates
          const exists = prev.some(msg => msg.id === data.message!.id);
          if (exists) return prev;
          
          // Remove optimistic message if this is the real version
          // (optimistic messages have temp IDs > 1000000000000, real IDs are smaller)
          const filtered = prev.filter(msg => {
            // If this is our own message (same sender, same content, within 5 seconds), remove optimistic version
            if (msg.sender_id === data.message!.sender_id && 
                msg.content === data.message!.content &&
                msg.id > 1000000000000) { // Optimistic message has temp ID
              const timeDiff = Math.abs(new Date(msg.created_at).getTime() - new Date(data.message!.created_at).getTime());
              if (timeDiff < 5000) { // Within 5 seconds
                return false; // Remove optimistic message
              }
            }
            return true;
          });
          
          return [...filtered, data.message!];
        });
        scrollToBottom();
      }
      
      // Always invalidate messages query for this conversation to ensure consistency
      queryClient.invalidateQueries({ queryKey: ["messages", data.conversation_id] });
    }
    // Invalidate conversations to update unread counts and last message
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
  }, [selectedConversation?.id, queryClient, scrollToBottom]);

  const handleTyping = useCallback((data: WebSocketMessage) => {
    if (data.conversation_id === selectedConversation?.id && data.user_id !== parseInt(user?.id || "0")) {
      if (data.is_typing) {
        setTypingUsers((prev) => new Set([...prev, data.user_id!]));
      } else {
        setTypingUsers((prev) => {
          const newSet = new Set(prev);
          newSet.delete(data.user_id!);
          return newSet;
        });
      }
    }
  }, [selectedConversation?.id, user?.id]);

  const handleConnection = useCallback((data: WebSocketMessage) => {
    if (data.status === "connected") {
      console.log("WebSocket connected successfully");
    }
  }, []);

  // Connect WebSocket on mount
  useEffect(() => {
    if (user?.id) {
      const userId = parseInt(user.id);
      chatWebSocket.connect(userId).catch((error) => {
        console.error("Failed to connect WebSocket:", error);
        toast.error("Failed to connect to chat. Please refresh the page.");
      });

      // Set up message handlers
      chatWebSocket.on("message", handleWebSocketMessage);
      chatWebSocket.on("typing", handleTyping);
      chatWebSocket.on("connection", handleConnection);

      return () => {
        chatWebSocket.off("message", handleWebSocketMessage);
        chatWebSocket.off("typing", handleTyping);
        chatWebSocket.off("connection", handleConnection);
        chatWebSocket.disconnect();
      };
    }
  }, [user?.id, handleWebSocketMessage, handleTyping, handleConnection]);

  // Fetch conversations (WebSocket will handle real-time updates)
  const { data: conversationsData, isLoading: isLoadingConversations } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => apiClient.getConversations(),
    // No polling - WebSocket handles real-time updates
  });

  // Fetch messages for selected conversation
  const { data: messagesData, isLoading: isLoadingMessages } = useQuery({
    queryKey: ["messages", selectedConversation?.id],
    queryFn: () => apiClient.getMessages(selectedConversation!.id),
    enabled: !!selectedConversation,
  });

  useEffect(() => {
    if (messagesData) {
      // Merge with existing messages to preserve optimistic updates
      setMessages((prev) => {
        // Create a map of existing messages by ID
        const existingMap = new Map(prev.map(msg => [msg.id, msg]));
        
        // Track optimistic messages (those with temp IDs)
        const optimisticMessages = prev.filter(msg => msg.id > 1000000000000);
        
        // Add or update messages from the query
        messagesData.forEach(msg => {
          existingMap.set(msg.id, msg);
          
          // Remove optimistic message if real message matches (same sender, same content, within 5 seconds)
          optimisticMessages.forEach(optMsg => {
            if (optMsg.sender_id === msg.sender_id && 
                optMsg.content === msg.content) {
              const timeDiff = Math.abs(new Date(optMsg.created_at).getTime() - new Date(msg.created_at).getTime());
              if (timeDiff < 5000) { // Within 5 seconds
                existingMap.delete(optMsg.id); // Remove optimistic message
              }
            }
          });
        });
        
        // Convert back to array and sort by created_at
        const merged = Array.from(existingMap.values());
        merged.sort((a, b) => 
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
        
        return merged;
      });
      scrollToBottom();
      // Mark as read
      if (selectedConversation) {
        chatWebSocket.sendReadReceipt(selectedConversation.id);
      }
    }
  }, [messagesData, selectedConversation, scrollToBottom]);

  // Fetch available users for new chat
  const { data: availableUsers } = useQuery({
    queryKey: ["chat-users"],
    queryFn: () => apiClient.getChatUsers(),
  });

  const createConversationMutation = useMutation({
    mutationFn: (participantIds: number[]) => apiClient.createConversation(participantIds),
    onSuccess: (newConversation) => {
      // Invalidate and refetch conversations to ensure both users see it
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.refetchQueries({ queryKey: ["conversations"] });
      setSelectedConversation(newConversation);
      setNewChatDialogOpen(false);
      setSelectedUsers([]);
      toast.success("Conversation created");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create conversation");
    },
  });


  const handleSendMessage = () => {
    if (!messageInput.trim() || !selectedConversation) return;

    const messageContent = messageInput.trim();
    const tempId = Date.now(); // Temporary ID for optimistic update
    
    // Optimistic update: add message to UI immediately
    const optimisticMessage: ChatMessage = {
      id: tempId,
      conversation_id: selectedConversation.id,
      sender_id: parseInt(user?.id || "0"),
      sender_name: user?.full_name || "You",
      sender_email: user?.email || "",
      content: messageContent,
      is_read: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    setMessages((prev) => [...prev, optimisticMessage]);
    setMessageInput("");
    setIsTyping(false);
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Send via WebSocket
    chatWebSocket.sendMessage(selectedConversation.id, messageContent);
    
    // Scroll to bottom after optimistic update
    scrollToBottom();
  };

  const handleInputChange = (value: string) => {
    setMessageInput(value);

    if (!isTyping && selectedConversation) {
      setIsTyping(true);
      chatWebSocket.sendTyping(selectedConversation.id, true);
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      if (selectedConversation) {
        chatWebSocket.sendTyping(selectedConversation.id, false);
      }
    }, 1000);
  };

  const handleCreateConversation = () => {
    if (selectedUsers.length === 0) {
      toast.error("Please select at least one user");
      return;
    }
    createConversationMutation.mutate(selectedUsers);
  };

  const getConversationName = (conversation: Conversation): string => {
    if (conversation.name) return conversation.name;
    if (conversation.is_group) {
      return conversation.participants.map((p) => p.name).join(", ");
    }
    const otherParticipant = conversation.participants.find(
      (p) => p.id !== parseInt(user?.id || "0")
    );
    return otherParticipant?.name || "Unknown";
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 sm:space-y-8">
        {/* Header */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-6 sm:p-8 border border-border/40">
          <div className="relative z-10">
            <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Messages
            </h1>
            <p className="text-sm sm:text-base text-muted-foreground">Internal team communication</p>
          </div>
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
        </div>
      </div>
      <div className="flex h-[calc(100vh-240px)] sm:h-[calc(100vh-280px)] gap-4 mt-6">
        {/* Conversations List */}
        <Card className="w-80 flex flex-col">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold">Messages</h2>
            <Button
              size="sm"
              onClick={() => setNewChatDialogOpen(true)}
              className="h-8 w-8 p-0"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          <ScrollArea className="flex-1">
            {isLoadingConversations ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : conversationsData?.conversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 text-center">
                <MessageCircle className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No conversations yet</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  onClick={() => setNewChatDialogOpen(true)}
                >
                  Start a conversation
                </Button>
              </div>
            ) : (
              <div className="p-2">
                {conversationsData?.conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => setSelectedConversation(conv)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors mb-2 ${
                      selectedConversation?.id === conv.id
                        ? "bg-primary/10 border border-primary"
                        : "hover:bg-muted"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{getConversationName(conv)}</p>
                        {conv.last_message && (
                          <p className="text-sm text-muted-foreground truncate">
                            {conv.last_message.content}
                          </p>
                        )}
                      </div>
                      {conv.unread_count > 0 && (
                        <Badge variant="default" className="ml-2">
                          {conv.unread_count}
                        </Badge>
                      )}
                    </div>
                    {conv.last_message && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatDistanceToNow(new Date(conv.last_message.created_at), {
                          addSuffix: true,
                        })}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </Card>

        {/* Chat Area */}
        <Card className="flex-1 flex flex-col">
          {selectedConversation ? (
            <>
              <div className="p-4 border-b">
                <h3 className="font-semibold">{getConversationName(selectedConversation)}</h3>
                <p className="text-sm text-muted-foreground">
                  {selectedConversation.participants.length} participant
                  {selectedConversation.participants.length !== 1 ? "s" : ""}
                </p>
              </div>
              <ScrollArea className="flex-1 p-4">
                {isLoadingMessages ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <>
                    {messages.map((message) => {
                      const isOwn = message.sender_id === parseInt(user?.id || "0");
                      return (
                        <div
                          key={message.id}
                          className={`flex mb-4 ${isOwn ? "justify-end" : "justify-start"} animate-fade-in`}
                        >
                          <div
                            className={`max-w-[70%] sm:max-w-[75%] rounded-lg p-3 shadow-sm transition-all duration-200 hover:shadow-md ${
                              isOwn
                                ? "bg-primary text-primary-foreground rounded-br-sm"
                                : "bg-muted rounded-bl-sm"
                            }`}
                          >
                            {!isOwn && (
                              <p className="text-xs font-medium mb-1 opacity-80">
                                {message.sender_name}
                              </p>
                            )}
                            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>
                            <p className="text-xs mt-1.5 opacity-70">
                              {format(new Date(message.created_at), "HH:mm")}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                    {typingUsers.size > 0 && (
                      <div className="flex justify-start mb-4">
                        <div className="bg-muted rounded-lg p-3">
                          <p className="text-sm text-muted-foreground italic">Typing...</p>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </ScrollArea>
              <div className="p-4 border-t">
                <div className="flex gap-2">
                  <Input
                    placeholder="Type a message..."
                    value={messageInput}
                    onChange={(e) => handleInputChange(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                  />
                  <Button onClick={handleSendMessage} disabled={!messageInput.trim()}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <MessageCircle className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Select a conversation to start chatting</p>
              </div>
            </div>
          )}
        </Card>

        {/* New Chat Dialog */}
        <Dialog open={newChatDialogOpen} onOpenChange={setNewChatDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New Conversation</DialogTitle>
              <DialogDescription>Select users to start a conversation</DialogDescription>
            </DialogHeader>
            <ScrollArea className="max-h-96">
              {availableUsers?.map((chatUser) => (
                <div
                  key={chatUser.id}
                  onClick={() => {
                    setSelectedUsers((prev) =>
                      prev.includes(parseInt(chatUser.id))
                        ? prev.filter((id) => id !== parseInt(chatUser.id))
                        : [...prev, parseInt(chatUser.id)]
                    );
                  }}
                  className={`p-3 rounded-lg cursor-pointer mb-2 ${
                    selectedUsers.includes(parseInt(chatUser.id))
                      ? "bg-primary/10 border border-primary"
                      : "hover:bg-muted"
                  }`}
                >
                  <p className="font-medium">{chatUser.full_name}</p>
                  <p className="text-sm text-muted-foreground">{chatUser.email}</p>
                </div>
              ))}
            </ScrollArea>
            <DialogFooter>
              <Button variant="outline" onClick={() => setNewChatDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreateConversation}
                disabled={selectedUsers.length === 0 || createConversationMutation.isPending}
              >
                {createConversationMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Create"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

