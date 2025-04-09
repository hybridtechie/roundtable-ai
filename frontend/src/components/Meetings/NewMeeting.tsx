import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { getQuestions, createMeeting } from "@/lib/api"
import { useAuth } from "@/context/AuthContext"
import { toast } from "@/components/ui/sonner"
import { X } from "lucide-react"
import {
  Participant,
} from "@/types/types"
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from "@dnd-kit/core"
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { Textarea } from "@/components/ui/textarea"


interface WeightedParticipant {
  id: string
  name: string
  weight: number
}

// Question interface for drag and drop
interface QuestionItem {
  id: string;
  content: string;
  isCustom: boolean;
}

// Sortable Participant Item Component
const SortableParticipant: React.FC<{
  participant: WeightedParticipant
  updateWeight: (id: string, weight: number) => void
}> = ({ participant, updateWeight }) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: participant.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="flex items-center justify-between p-2 bg-gray-100 rounded cursor-move">
      <span>{participant.name}</span>
      <input
        type="number"
        min="1"
        max="10"
        value={participant.weight}
        onChange={(e) => updateWeight(participant.id, parseInt(e.target.value))}
        className="w-16 p-1 border rounded"
      />
    </li>
  )
}

// Sortable Question Item Component
const SortableQuestion: React.FC<{
  question: QuestionItem;
  onRemove: (id: string) => void;
}> = ({ question, onRemove }) => {
  // For the sortable functionality
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: question.id
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  // Handle remove button click
  const handleRemoveClick = (e: React.MouseEvent) => {
    // Stop propagation to prevent drag events from interfering
    e.stopPropagation();
    onRemove(question.id);
  };

  return (
    <div className="flex items-center justify-between p-2 mb-2 bg-gray-100 rounded">
      <div
        ref={setNodeRef}
        style={style}
        {...attributes}
        {...listeners}
        className="flex-grow cursor-move"
      >
        <span>{question.content}</span>
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={handleRemoveClick}
        className="w-8 h-8 ml-2 rounded-full"
        type="button"
      >
        <X className="w-4 h-4" />
        <span className="sr-only">Remove</span>
      </Button>
    </div>
  );
};

const NewMeeting: React.FC = () => {
  const navigate = useNavigate()
  const [step, setStep] = useState<"group" | "participants" | "questions">("group")
  const { state } = useAuth()
  const [selectedGroup, setSelectedGroup] = useState<string>("")
  const [discussionStrategy, setDiscussionStrategy] = useState<string>("round robin")
  const [topic, setTopic] = useState<string>("")
  const groups = state.backendUser?.groups || []
  
  interface ExtendedParticipant extends WeightedParticipant {
    persona_description: string
    role: string
  }

  const [participants, setParticipants] = useState<ExtendedParticipant[]>([])
  const [aiQuestions, setAiQuestions] = useState<string[]>([])
  const [isQuestionsLoading, setIsQuestionsLoading] = useState(false)
  const [finalQuestions, setFinalQuestions] = useState<QuestionItem[]>([])
  const [newCustomQuestion, setNewCustomQuestion] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)

  // Setup sensors for drag-and-drop
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  )

  // Handle group selection
  const handleGroupSelect = (groupId: string) => {
    setSelectedGroup(groupId)
    setParticipants([]) // Clear participants before setting new ones
    
    const selectedGroupData = groups.find(g => g.id === groupId)
    if (!selectedGroupData) return;

    // Create a map of all participants from state
    const allParticipants = state.backendUser?.participants || [];
    const participantsMap = new Map(allParticipants.map(p => [p.id, p]));

    // Get participant IDs from the group
    let participantIds: string[] = [];
    if (Array.isArray(selectedGroupData.participant_ids)) {
      participantIds = selectedGroupData.participant_ids;
    } else if (Array.isArray(selectedGroupData.participants)) {
      participantIds = selectedGroupData.participants.map(p => p?.id).filter((id): id is string => !!id);
    }

    // Look up full participant details from the map and convert to ExtendedParticipant
    const groupParticipants = participantIds
      .map(id => participantsMap.get(id))
      .filter((p): p is Participant => !!p)
      .map(p => ({
        id: p.id,
        name: p.name,
        role: p.role,
        weight: 5, // Default weight
        persona_description: p.role_overview || "Participant",
      }));

    setParticipants(groupParticipants);
  }

  // Fetch groups on mount and set default group
  // Set default group on initial render
  useEffect(() => {
    if (groups.length > 0 && !selectedGroup) {
      const defaultGroup = groups[0]
      handleGroupSelect(defaultGroup.id)
    }
  }, [groups, selectedGroup])

  // Fetch questions when moving to next step
  const handleNextFromGroup = async () => {
    if (!selectedGroup || !topic.trim()) return
    
    // Move to participants step first
    setStep("participants")
    
    // Then fetch questions in the background
    try {
      setIsQuestionsLoading(true)
      const response = await getQuestions(topic, selectedGroup)
      setAiQuestions(response.data.questions)
    } catch (error) {
      console.error("Error fetching questions:", error)
      toast.error("Failed to fetch questions")
    } finally {
      setIsQuestionsLoading(false)
    }
  }

  // Handle drag-and-drop reordering for participants
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (active.id !== over?.id) {
      setParticipants((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id)
        const newIndex = items.findIndex((item) => item.id === over?.id)
        return arrayMove(items, oldIndex, newIndex)
      })
    }
  }
  
  // Handle drag-and-drop for questions
  const handleQuestionDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    
    if (active.id !== over?.id) {
      // If it's a reordering within the final list
      if (finalQuestions.some(q => q.id === active.id) && finalQuestions.some(q => q.id === over?.id)) {
        setFinalQuestions((items) => {
          const oldIndex = items.findIndex((item) => item.id === active.id);
          const newIndex = items.findIndex((item) => item.id === over?.id);
          return arrayMove(items, oldIndex, newIndex);
        });
      }
    }
  };
  
  // Add a question to the final list
  const addToFinalList = (content: string, isCustom: boolean = false) => {
    if (finalQuestions.length >= 5) return;
    
    // Check if question already exists in final list
    if (finalQuestions.some(q => q.content === content)) return;
    
    const newQuestion: QuestionItem = {
      id: `question-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      content,
      isCustom
    };
    
    setFinalQuestions(prev => [...prev, newQuestion]);
    
    // If it's an AI-generated question, remove it from the AI questions list
    if (!isCustom) {
      setAiQuestions(prev => prev.filter(q => q !== content));
    }
  };
  
  // Remove a question from the final list
  const removeFromFinalList = (id: string) => {
    const questionToRemove = finalQuestions.find(q => q.id === id);
    if (questionToRemove) {
      setFinalQuestions(prev => prev.filter(q => q.id !== id));
    }
  };

  // Update participant weight
  const updateWeight = (id: string, weight: number) => {
    setParticipants((prev) => prev.map((p) => (p.id === id ? { ...p, weight: Math.max(1, Math.min(10, weight)) } : p)))
  }

  // Add custom question
  const addCustomQuestion = () => {
    if (newCustomQuestion.trim() && finalQuestions.length < 5) {
      addToFinalList(newCustomQuestion.trim(), true);
      setNewCustomQuestion("");
    }
  };

  const handleBackFromParticipants = () => {
    setStep("group")
  }

  const handleNextFromParticipants = () => {
    if (participants.length > 0) {
      setStep("questions")
      // Clear any existing questions when moving to questions step
      setFinalQuestions([])
    }
  }

  const handleStartChat = async () => {
    if (!selectedGroup || !topic.trim()) return

    setIsLoading(true)

    try {
      // Create meeting and get meeting_id
      const response = await createMeeting({
        group_id: selectedGroup,
        strategy: discussionStrategy,
        topic: topic,
        questions: finalQuestions.map(q => q.content),
        participant_order: participants.map((participant, index) => ({
          participant_id: participant.id,
          weight: participant.weight,
          order: index + 1,
        })),
      })
      
      if (!response.data.id) {
        throw new Error('No meeting ID returned from server');
      }
      
      toast.success("Meeting created successfully")
      
      // Navigate to the Chat component with the meeting ID, matching NewChat.tsx pattern
      navigate(`/chat/${response.data.id}/stream`)
    } catch (error) {
      console.error("Error creating meeting:", error)
      toast.error("Failed to create meeting")
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] p-4">
      {step === "group" && (
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <h2 className="text-2xl font-bold">Step 1: Choose Participants</h2>
          <div className="flex flex-col items-start w-[70%]">
            <label className="mb-2 text-lg font-semibold">Participant Group</label>
            <Select value={selectedGroup} onValueChange={handleGroupSelect}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a Participant Group" />
              </SelectTrigger>
              <SelectContent>
                {groups.map((group) => (
                  <SelectItem key={group.id} value={group.id}>
                    {group.name || group.id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col items-start w-[70%] mt-4">
            <label className="mb-2 text-lg font-semibold">Discussion Strategy</label>
            <Select value={discussionStrategy} onValueChange={setDiscussionStrategy}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a Strategy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="round robin">Round Robin</SelectItem>
                <SelectItem value="opinionated">Opinionated</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col items-start w-[70%] mt-4">
            <label className="mb-2 text-lg font-semibold">Topic</label>
            <Textarea
              placeholder="Enter your message"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="flex-1 min-h-[60px]"
              rows={4}
            />
          </div>
          <div className="flex flex-row w-[70%] mt-4">
            <Button
              onClick={handleNextFromGroup}
              disabled={!selectedGroup || !topic.trim()}
              className="text-white bg-blue-500 hover:bg-blue-600">
              Next
            </Button>
          </div>
        </div>
      )}

      {step === "participants" && (
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <h2 className="text-2xl font-bold">Step 2: Order Participants & Assign Weights</h2>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={participants.map((p) => p.id)} strategy={verticalListSortingStrategy}>
              <ul className="w-[70%] space-y-2">
                {participants.map((participant) => (
                  <SortableParticipant key={participant.id} participant={participant} updateWeight={updateWeight} />
                ))}
              </ul>
            </SortableContext>
          </DndContext>
          <div className="flex flex-row w-[70%] mt-4 justify-between">
            <Button onClick={handleBackFromParticipants} className="text-white bg-blue-500 hover:bg-blue-600">
              Back
            </Button>
            <Button onClick={handleNextFromParticipants} className="text-white bg-blue-500 hover:bg-blue-600">
              Next
            </Button>
          </div>
        </div>
      )}

      {step === "questions" && (
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <h2 className="text-2xl font-bold">Step 3: Select or Create Questions</h2>
          
          {/* Final Questions List (Drag to reorder) */}
          <div className="w-[70%] space-y-4 mb-4">
            <h3 className="text-lg font-semibold">Final Questions List ({finalQuestions.length}/5)</h3>
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleQuestionDragEnd}>
              <SortableContext items={finalQuestions.map(q => q.id)} strategy={verticalListSortingStrategy}>
                <ul className="w-full min-h-[100px] border border-dashed border-gray-300 p-4 rounded-md">
                  {finalQuestions.length === 0 ? (
                    <li className="text-center text-gray-400">Drag questions here or add your own (max 5)</li>
                  ) : (
                    finalQuestions.map((question) => (
                      <SortableQuestion
                        key={question.id}
                        question={question}
                        onRemove={removeFromFinalList}
                      />
                    ))
                  )}
                </ul>
              </SortableContext>
            </DndContext>
          </div>
          
          {/* Custom Questions Input */}
          <div className="w-[70%] space-y-4 mb-4">
            <h3 className="text-lg font-semibold">Add Your Own Question</h3>
            <div className="flex space-x-2">
              <Textarea
                placeholder="Enter your custom question"
                value={newCustomQuestion}
                onChange={(e) => setNewCustomQuestion(e.target.value)}
                className="flex-1"
              />
              <Button
                onClick={addCustomQuestion}
                disabled={!newCustomQuestion.trim() || finalQuestions.length >= 5}
                className="whitespace-nowrap"
              >
                Add Question
              </Button>
            </div>
          </div>

          {/* AI Generated Questions */}
          <div className="w-[70%] space-y-2">
            <h3 className="mb-2 text-lg font-semibold">AI Generated Questions</h3>
            <div className="space-y-2 max-h-[300px] overflow-y-auto p-2 border border-gray-200 rounded-md">
              {isQuestionsLoading ? (
                <div className="flex justify-center items-center h-[100px]">
                  <LoadingSpinner />
                </div>
              ) : aiQuestions.length === 0 ? (
                <div className="py-4 text-center text-gray-400">
                  No AI-generated questions available
                </div>
              ) : (
                aiQuestions.map((question) => (
                  <div
                    key={question}
                    className="flex items-center justify-between p-2 rounded bg-gray-50 hover:bg-gray-100"
                    draggable
                    onDragStart={(e) => {
                      e.dataTransfer.setData("text/plain", question);
                    }}
                  >
                    <span>{question}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => addToFinalList(question)}
                      disabled={finalQuestions.length >= 5 || finalQuestions.some(q => q.content === question)}
                    >
                      Add to List
                    </Button>
                  </div>
                ))
              )}
            </div>
          </div>
          
          <div className="flex flex-col w-[70%] gap-2">
            <p className="text-sm text-gray-600">
              Selected {finalQuestions.length} of 5 questions
              {finalQuestions.filter(q => q.isCustom).length > 0 &&
                ` (${finalQuestions.filter(q => q.isCustom).length} custom)`}
            </p>
            <Button
              onClick={handleStartChat}
              disabled={finalQuestions.length === 0 || isLoading}
              className="text-white bg-blue-500 hover:bg-blue-600">
              {isLoading ? "Creating Meeting..." : "Start Meeting"}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default NewMeeting
