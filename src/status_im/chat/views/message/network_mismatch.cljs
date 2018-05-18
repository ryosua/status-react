(ns status-im.chat.views.message.network-mismatch
  (:require [status-im.i18n :as i18n]
            [status-im.chat.styles.message.message :as styles]
            [status-im.ui.components.colors :as colors]
            [status-im.ui.components.react :as react]
            [status-im.ui.components.icons.vector-icons :as vector-icons]))

(defn view [request-network]
  [react/view styles/network-mismatch-view
   [react/text
    request-network]
   [react/view styles/network-mismatch-icon-view
    [vector-icons/icon :icons/warning styles/network-mismatch-icon]]
   [react/text {:style styles/network-mismatch-text}
    (i18n/label :network-mismatch)]])
