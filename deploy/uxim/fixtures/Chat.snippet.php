<?php
class Chat {
    public function getUserRooms() {
        $userID = Request::instance()->user_id;
        $currentUser = Request::instance()->user;
        foreach ($userRooms as $userRoom) {
            $lastMessage = ChatMessage::where('room_id', $userRoom->room_id)->find();
            if ($lastMessage) {
                $lastMessageData = $lastMessage->toArray();
                $lastMessageData['content_raw'] = htmlspecialchars($lastMessageData['content'], ENT_QUOTES, 'UTF-8');
            }
            // 获取未读消息数
            $unreadCount = ChatMessage::where('room_id', $userRoom->room_id)
                ->where('from_user', '<>', $userID)
                ->where('created_at', '>', $userRoom->joined_at)
                ->count();
        }
    }
    public function getRoomMembers($room_id) {
        $memberDetails[] = [
            'role'      => $member->role,
            'joined_at' => $member->joined_at->format('Y-m-d H:i:s'),
        ];
    }
}
