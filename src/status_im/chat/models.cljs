(ns status-im.chat.models
  (:require [status-im.ui.components.styles :as styles]
            [status-im.utils.gfycat.core :as gfycat]
            [status-im.data-store.chats :as chats-store]
            [status-im.utils.handlers-macro :as handlers-macro]
            [status-im.data-store.messages :as messages-store]))

(defn set-chat-ui-props
  "Updates ui-props in active chat by merging provided kvs into them"
  [{:keys [current-chat-id] :as db} kvs]
  (update-in db [:chat-ui-props current-chat-id] merge kvs))

(defn toggle-chat-ui-prop
  "Toggles chat ui prop in active chat"
  [{:keys [current-chat-id] :as db} ui-element]
  (update-in db [:chat-ui-props current-chat-id ui-element] not))

(defn- create-new-chat
  [chat-id {:keys [db now]}]
  (let [name (get-in db [:contacts/contacts chat-id :name])]
    {:chat-id            chat-id
     :name               (or name (gfycat/generate-gfy chat-id))
     :color              styles/default-chat-color
     :group-chat         false
     :is-active          true
     :timestamp          now
     :contacts           [chat-id]
     :last-clock-value   0}))

(defn upsert-chat
  "Upsert chat when not deleted"
  [{:keys [chat-id] :as chat-props} {:keys [db] :as cofx}]
  (let [chat (merge
              (or (get (:chats db) chat-id)
                  (create-new-chat chat-id cofx))
              chat-props)]

    (if (:is-active chat)
      {:db            (update-in db [:chats chat-id] merge chat)
       :data-store/tx [(chats-store/save-chat-tx chat)]}
      ;; when chat is deleted, don't change anything
      {:db db})))

(defn add-public-chat
  "Adds new public group chat to db & realm"
  [topic cofx]
  (upsert-chat {:chat-id          topic
                :is-active        true
                :name             topic
                :group-chat       true
                :contacts         []
                :public?          true} cofx))

(defn add-group-chat
  "Adds new private group chat to db & realm"
  [chat-id chat-name admin participants cofx]
  (upsert-chat {:chat-id     chat-id
                :name        chat-name
                :is-active   true
                :group-chat  true
                :group-admin admin
                :contacts    participants} cofx))

(defn clear-history [chat-id {:keys [db] :as cofx}]
  (let [{:keys [messages
                removed-at-clock-value]} (get-in db [:chats chat-id])
        last-message-clock-value (or (->> messages
                                          vals
                                          (sort-by (comp unchecked-negate :clock-value))
                                          first
                                          :clock-value) removed-at-clock-value)]
    (-> {:db db}
        (assoc-in [:db :chats chat-id :messages] {})
        (assoc-in [:db :chats chat-id :deleted-at-clock-value] last-message-clock-value)
        (assoc :data-store/tx [(chats-store/clear-history-tx chat-id last-message-clock-value)
                               (messages-store/delete-messages-tx chat-id)]))))

(defn remove-chat [chat-id {:keys [db now] :as cofx}]
  (let [{:keys [chat-id group-chat debug?]} (get-in db [:chats chat-id])]
    (if debug?
      (handlers-macro/merge-fx cofx
                               (update-in [:db :chats] dissoc chat-id)
                               (assoc :data-store/tx [(chats-store/delete-chat-tx chat-id)
                                                      (messages-store/delete-messages-tx chat-id)]))
      (handlers-macro/merge-fx (assoc-in {:db db
                                          :data-store/tx [(chats-store/deactivate-chat-tx chat-id now)]}
                                         [:db :chats chat-id :is-active] false)
                               (clear-history chat-id)))))

(defn bot-only-chat? [db chat-id]
  (let [{:keys [group-chat contacts]} (get-in db [:chats chat-id])]
    (and (not group-chat)
         (get-in db [:contacts/contacts (first contacts) :dapp?]))))
