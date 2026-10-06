import React, { useEffect, useState } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import ContentLayout from '@cloudscape-design/components/content-layout';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import LiveRegion from '@cloudscape-design/components/live-region';
import Link from '@cloudscape-design/components/link';
import Box from '@cloudscape-design/components/box';
import ChatBubble from '@cloudscape-design/chat-components/chat-bubble';
import Avatar from '@cloudscape-design/chat-components/avatar';
import { buyer, question, activity, answer } from './conversation.js';

// How long the search shows as in progress. Cloudscape advises against
// loading states shorter than one second.
const SEARCH_DURATION_MS = 2000;

// Add ?state=searching to the URL to hold the page on the in-progress state.
const holdSearching = new URLSearchParams(window.location.search).get('state') === 'searching';

// Turns each URL in the answer into a link. The link text stays the URL,
// so the answer reads exactly as the agent wrote it. Punctuation at the end
// of a URL, like a period or closing parenthesis, stays outside the link.
function AnswerText({ text }) {
  return text.split(/(https:\/\/\S+)/).map((part, i) => {
    if (!part.startsWith('https://')) {
      return <React.Fragment key={i}>{part}</React.Fragment>;
    }
    const [, url, trailing] = part.match(/^(.*?)([.,;:!?)]*)$/);
    return (
      <React.Fragment key={i}>
        <Link href={url} variant="primary" external externalIconAriaLabel="Opens in a new tab">
          {url}
        </Link>
        {trailing}
      </React.Fragment>
    );
  });
}

export default function App() {
  const [searching, setSearching] = useState(true);
  // Starts empty and fills in after the first render. Screen readers often
  // skip live region text that is already there when the page loads.
  const [announcement, setAnnouncement] = useState('');

  useEffect(() => {
    if (holdSearching) return;
    const timer = setTimeout(() => setSearching(false), SEARCH_DURATION_MS);
    return () => clearTimeout(timer);
  }, []);

  const activityText = (step) => `${searching ? step.inProgressLabel : step.doneLabel}: ${step.query}`;
  const activitySummary = activity.map(activityText).join('. ');

  useEffect(() => {
    setAnnouncement(searching ? activitySummary : `${activitySummary}. Response received.`);
  }, [searching, activitySummary]);

  return (
    <AppLayout
      navigationHide
      toolsHide
      maxContentWidth={800}
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description={`Concept prototype, not affiliated with AWS. Sample conversation for ${buyer.name}, a buyer in the ${buyer.experience} experience. All data is fictional.`}
            >
              Private catalog buyer agent
            </Header>
          }
        >
          <Container
            footer={
              <Box variant="small" color="text-body-secondary">
                Responses can include mistakes. Check product details before you subscribe.
              </Box>
            }
          >
            <div role="region" aria-label="Conversation">
              <SpaceBetween size="l">
                <ChatBubble
                  type="outgoing"
                  ariaLabel={`${buyer.name} message`}
                  avatar={<Avatar ariaLabel={buyer.name} tooltipText={buyer.name} initials={buyer.name[0]} />}
                >
                  {question}
                </ChatBubble>

                <ChatBubble
                  type="incoming"
                  ariaLabel="Generative AI assistant response"
                  avatar={
                    <Avatar
                      ariaLabel="Generative AI assistant"
                      tooltipText="Generative AI assistant"
                      iconName="gen-ai"
                      color="gen-ai"
                      loading={searching}
                    />
                  }
                >
                  <SpaceBetween size="s">
                    {/* While searching, follow Cloudscape's gen AI loading pattern: the
                        avatar's loading state plus plain loading text, no second spinner. */}
                    {activity.map((step) =>
                      searching ? (
                        <Box key={step.id} color="text-status-inactive">
                          {activityText(step)}
                        </Box>
                      ) : (
                        <StatusIndicator key={step.id} type="success" iconAriaLabel="Completed">
                          {activityText(step)}
                        </StatusIndicator>
                      )
                    )}
                    {!searching && (
                      <Box variant="p">
                        <AnswerText text={answer} />
                      </Box>
                    )}
                  </SpaceBetween>
                </ChatBubble>
              </SpaceBetween>
            </div>
            <LiveRegion hidden>{announcement}</LiveRegion>
          </Container>
        </ContentLayout>
      }
    />
  );
}
