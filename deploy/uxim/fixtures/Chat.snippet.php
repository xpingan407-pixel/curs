<?php
// Minimal excerpt for patch tests
class Chat {
    public function getUserRooms() {
        $userID = Request::instance()->user_id;
        $currentUser = Request::instance()->user;
        foreach ($userRooms as $userRoom) {
            // 获取未读消息数
            $excludeSenderId = ($currentUser && isset($currentUser->id))
                ? (int) $currentUser->id
                : (int) (User::where('user_id', $userID)->value('id') ?: 0);
            $unreadQuery = ChatMessage::where('room_id', $userRoom->room_id)
                ->where('sender_id', '<>', $excludeSenderId);
            if ($userRoom->joined_at) {
                $unreadQuery->where('created_at', '>', $userRoom->joined_at);
            }
            $unreadCount = $unreadQuery->count();

            $rooms[] = [
                'joined_at'    => $userRoom->joined_at
                    ? (is_object($userRoom->joined_at)
                        ? $userRoom->joined_at->format('Y-m-d H:i:s')
                        : (string) $userRoom->joined_at)
                    : null,
            ];
        }
    }
    public function getRoomMembers($room_id) {
        $memberDetails[] = [
            'role'      => $member->role ?? 'member',
            'joined_at' => $member->joined_at
                    ? (is_object($member->joined_at)
                        ? $member->joined_at->format('Y-m-d H:i:s')
                        : (string) $member->joined_at)
                    : null,
        ];
    }
}
